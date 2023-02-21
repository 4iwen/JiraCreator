def get_projects(jira):
    projects = []
    for proj in jira.projects():
        projects.append({'key': proj.key, 'name': proj.name})

    return projects


def get_issue_types(jira, project):
    issue_types = jira.project(project).raw['issueTypes']
    types = []
    for i_type in issue_types:
        types.append(i_type['name'])

    return types


def get_assignees(jira, project):
    assignees = []
    for assignee in jira.search_assignable_users_for_projects(username='', projectKeys=project, maxResults=0):
        assignees.append(assignee)
    return assignees


def get_order_types(jira, project):
    issues = jira.search_issues('project = ' + str(project), maxResults=1)
    if len(issues) == 0:
        return []
    issue = issues[0]
    order_types_json = jira.editmeta(issue)['fields']['customfield_12400']['allowedValues']
    order_types = []

    for order_type in order_types_json:
        order_types.append({'id': int(order_type['id']), 'name': order_type['value']})

    return order_types


def get_sprints(jira, project):
    boards = jira.boards(maxResults=0, projectKeyOrID=project)
    sprints = []

    for board in boards:
        for sprint in jira.sprints(board_id=board.id, maxResults=0):
            if sprint.state == 'active' or sprint.state == 'future':
                sprints.append({'id': int(sprint.id), 'name': sprint.name})

    # remove duplicates
    sprints = [dict(t) for t in {tuple(d.items()) for d in sprints}]

    return sprints
