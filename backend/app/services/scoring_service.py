from app.models import Score, Scan, Codebase, User, Team, Project, UserRole

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
        members = db.query(User).filter(User.team_id == team_id, User.role == UserRole.PROGRAMMER).all()
        for user in members:
            query = db.query(Score).join(Scan).join(Codebase).filter(Score.programmer_id == user.user_id)
            if project_id is not None:
                query = query.filter(Codebase.project_id == project_id)
                if not db.query(Codebase).filter(Codebase.owner_id == user.user_id, Codebase.project_id == project_id).first():
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
        teams = db.query(Team).join(User, User.team_id == Team.team_id).join(
            Codebase, Codebase.owner_id == User.user_id).filter(Codebase.project_id == project_id).distinct().all()
        rows, weighted, weight = [], 0, 0
        for team in teams:
            data = cls.aggregate_team_scores(db, team.team_id, project_id)
            size = data["functions_count"]
            weighted += (data["average_documentation_score"] or 0) * size
            weight += size
            rows.append({"team_id": str(team.team_id), "team_name": team.team_name,
                         "average_score": data["average_documentation_score"],
                         "functions_count": size, "programmers_count": data["programmers_count"]})
        rows.sort(key=lambda r: (r["average_score"] is not None, r["average_score"] or 0), reverse=True)
        return {"project_id": str(project_id), "project_name": project.project_name,
                "average_project_score": round(weighted / weight, 2) if weight else None,
                "teams_count": len(rows), "ranked_teams": rows}

