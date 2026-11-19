from app.models import Score, Scan, Codebase, User, Team, Project, UserRole, TeamMembership, MembershipStatus
from sqlalchemy import or_
from app.access import codebases_in_team

class ScoringService:
    SEVERITY_PENALTIES = {"High": 4.0, "Medium": 2.0, "Low": 1.0}

    @classmethod
    def calculate_drs(cls, total_functions, documented_functions, findings_by_severity=None, findings=None):
        if not 0 <= documented_functions <= total_functions:
            raise ValueError("Invalid function counts")
        if not total_functions:
            return {"documentation_score": None, "code_quality_score": None,
                    "breakdown": {"total_functions": 0, "documented_functions": 0, "note": "Not applicable: no functions found."}}
        ratio = documented_functions / total_functions
        parameter_penalty = return_penalty = 0.0
        if findings is not None:
            for finding in findings:
                if finding.type == "Missing Documentation":
                    continue
                penalty = cls.SEVERITY_PENALTIES[finding.severity]
                if "Parameter" in finding.type:
                    parameter_penalty += penalty
                else:
                    return_penalty += penalty
        else:
            parameter_penalty = sum(cls.SEVERITY_PENALTIES.get(s, 1) * n for s, n in (findings_by_severity or {}).items())
        complete = 40 * ratio
        parameter = max(0, 40 - parameter_penalty) * ratio
        returns = max(0, 20 - return_penalty) * ratio
        score = round(complete + parameter + returns, 2)
        return {"documentation_score": score, "code_quality_score": score, "breakdown": {
            "policy": "DRS v1; severity penalties 4/2/1; AI excluded",
            "total_functions": total_functions, "documented_functions": documented_functions,
            "documentation_ratio": round(ratio, 4), "completeness_score": round(complete, 2),
            "parameter_consistency": round(parameter, 2), "return_consistency": round(returns, 2),
            "consistency_score": round(parameter + returns, 2),
            "scaled_penalties": round((min(40, parameter_penalty) + min(20, return_penalty)) * ratio, 2),
            "total_drs": score}}

    @classmethod
    def aggregate_team_scores(cls, db, team_id, project_id=None):
        team = db.get(Team, team_id)
        ranked = []
        weighted = weight = 0
        codebases = codebases_in_team(db, db.query(Codebase), team_id)
        if project_id is not None:
            codebases = codebases.filter(Codebase.project_id == project_id)
        owners = codebases.with_entities(Codebase.owner_id)
        approved_members = {row[0] for row in db.query(TeamMembership.programmer_id).filter_by(
            team_id=team_id, status=MembershipStatus.APPROVED).all()}
        members = db.query(User).filter(User.role == UserRole.PROGRAMMER,
            or_(User.user_id.in_(owners), User.user_id.in_(approved_members), User.team_id == team_id)).all()
        for user in members:
            query = db.query(Score).join(Scan).filter(Score.programmer_id == user.user_id,
                Scan.codebase_id.in_(codebases.with_entities(Codebase.codebase_id)))
            if project_id is not None:
                if not codebases.filter(Codebase.owner_id == user.user_id).first() and not (
                    team.project_id == project_id and user.user_id in approved_members):
                    continue
            # Latest scan per codebase avoids an unrelated codebase replacing a programmer's whole score.
            seen, subtotal, count = set(), 0, 0
            for score in query.order_by(Scan.timestamp.desc(), Scan.scan_id.desc()).all():
                if score.scan.codebase_id in seen:
                    continue
                seen.add(score.scan.codebase_id)
                size = score.breakdown.get("total_functions", 0)
                if score.documentation_score is not None:
                    subtotal += score.documentation_score * size
                    count += size
            value = round(subtotal / count, 2) if count else None
            weighted += subtotal
            weight += count
            ranked.append({"programmer_id": str(user.user_id), "name": user.name, "email": user.email,
                           "latest_score": value, "functions_count": count})
        ranked.sort(key=lambda r: (r["latest_score"] is not None, r["latest_score"] or 0), reverse=True)
        return {"team_id": str(team.team_id), "team_name": team.team_name,
                "average_documentation_score": round(weighted / weight, 2) if weight else None,
                "programmers_count": len(ranked), "functions_count": weight, "ranked_programmers": ranked}

    @classmethod
    def aggregate_project_scores(cls, db, project_id):
        project = db.get(Project, project_id)
        legacy_teams = db.query(User.team_id).join(Codebase, Codebase.owner_id == User.user_id).filter(
            Codebase.project_id == project_id, Codebase.team_id.is_(None))
        teams = db.query(Team).filter(or_(Team.project_id == project_id, Team.team_id.in_(legacy_teams))).all()
        rows, weighted, weight = [], 0, 0
        programmers = {}
        for team in teams:
            data = cls.aggregate_team_scores(db, team.team_id, project_id)
            size = data["functions_count"]
            weighted += (data["average_documentation_score"] or 0) * size
            weight += size
            rows.append({"team_id": str(team.team_id), "team_name": team.team_name,
                         "average_score": data["average_documentation_score"],
                         "functions_count": size, "programmers_count": data["programmers_count"]})
            for member in data["ranked_programmers"]:
                entry = programmers.setdefault(member["programmer_id"], {
                    "programmer_id": member["programmer_id"], "name": member["name"], "email": member["email"],
                    "teams": [], "functions_count": 0, "weighted_score": 0.0})
                entry["teams"].append({"team_id": str(team.team_id), "team_name": team.team_name})
                entry["functions_count"] += member["functions_count"]
                entry["weighted_score"] += (member["latest_score"] or 0) * member["functions_count"]
        rows.sort(key=lambda r: (r["average_score"] is not None, r["average_score"] or 0), reverse=True)
        ranked_programmers = []
        for entry in programmers.values():
            subtotal = entry.pop("weighted_score")
            entry["latest_score"] = round(subtotal / entry["functions_count"], 2) if entry["functions_count"] else None
            ranked_programmers.append(entry)
        ranked_programmers.sort(key=lambda r: (r["latest_score"] is not None, r["latest_score"] or 0), reverse=True)
        return {"project_id": str(project_id), "project_name": project.project_name,
                "average_project_score": round(weighted / weight, 2) if weight else None,
                "teams_count": len(rows), "ranked_teams": rows, "ranked_programmers": ranked_programmers}

