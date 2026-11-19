from app.models import Project, Codebase, Team, TeamMembership, MembershipStatus
from app.services.scoring_service import ScoringService
from tests.test_security_and_scans import upload, headers

def test_project_aggregation_never_counts_other_project(client, db_session, test_users, programmer_token):
    upload(client, programmer_token, test_users['codebase'], {'good.py': 'def good():\n    """No action."""\n    pass'})
    other_project=Project(project_name='Unrelated',project_lead_id=test_users['project_lead'].user_id)
    db_session.add(other_project);db_session.flush()
    other_team=Team(team_name='Other team',project_id=other_project.project_id,
                    team_lead_id=test_users['team_lead'].user_id)
    db_session.add(other_team);db_session.flush()
    other_codebase=Codebase(name='Other',owner_id=test_users['programmer'].user_id,
                           project_id=other_project.project_id,team_id=other_team.team_id)
    db_session.add(other_codebase)
    db_session.add(TeamMembership(team_id=other_team.team_id, programmer_id=test_users['programmer'].user_id,
                                 status=MembershipStatus.APPROVED, decided_by=test_users['team_lead'].user_id))
    db_session.commit()
    upload(client,programmer_token,other_codebase,{'bad.py':'def bad(): pass'})
    project=ScoringService.aggregate_project_scores(db_session,test_users['project'].project_id)
    assert project['average_project_score']==100
    assert project['ranked_teams'][0]['functions_count']==1
    team=ScoringService.aggregate_team_scores(db_session,test_users['team'].team_id)
    assert team['average_documentation_score']==100
    assert ScoringService.aggregate_team_scores(db_session,other_team.team_id)['average_documentation_score']==0

def test_latest_scan_per_codebase_replaces_previous(client,db_session,test_users,programmer_token):
    upload(client,programmer_token,test_users['codebase'],{'a.py':'def f(): pass'})
    upload(client,programmer_token,test_users['codebase'],{'a.py':'def f():\n    """No action."""\n    pass'})
    result=ScoringService.aggregate_team_scores(db_session,test_users['team'].team_id)
    assert result['average_documentation_score']==100
    assert result['functions_count']==1

def test_authorized_leads_can_inspect_scan(client,test_users,programmer_token,team_lead_token,project_lead_token):
    response=upload(client,programmer_token,test_users['codebase'],{'a.py':'def f(): pass'})
    sid=response.json()['scan_id']
    for token in (team_lead_token,project_lead_token):
        assert client.get(f'/api/v1/scans/{sid}/functions',headers=headers(token)).status_code==200
        assert len(client.get('/api/v1/codebases',headers=headers(token)).json())==1
