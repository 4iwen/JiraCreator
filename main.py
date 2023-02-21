import json
import copy
from flask import Flask, render_template, request, jsonify
from jira import JIRA
from waitress import serve

import utils

CONFIG = json.load(open('./config.json', 'r', encoding='utf-8'))
APP = Flask(__name__)
JIRA = JIRA(server=CONFIG['jira']['server'],
            basic_auth=(CONFIG['jira']['email'],
                        CONFIG['jira']['api_token']))


selected_project_key = None
projects = utils.get_projects(JIRA)
issue_types = []
assignees = []
sprints = []
order_types = []

tasks = []
variables = []


@APP.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@APP.errorhandler(400)
def bad_request(e):
    return render_template('400.html'), 400


@APP.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403


@APP.route('/')
def index():
    return render_template('index.html', projects=projects)


@APP.route('/creator')
def creator():
    project_key = request.args.get('project')

    # check if the project parameter is valid, if not, redirect to 400, if it is valid, set the selected project key
    if project_key not in [project['key'] for project in projects]:
        return render_template('400.html'), 400
    else:
        response = JIRA.my_permissions(projectKey=project_key, permissions='CREATE_ISSUES')
        # check if havePermission is True, if not, redirect to 403
        if not response['permissions']['CREATE_ISSUES']['havePermission']:
            return render_template('403.html'), 403

        update(project_key)
        project_name = [project['name'] for project in projects if project['key'] == project_key][0]
        global selected_project_key
        selected_project_key = project_key

    return render_template('creator.html',
                           project=project_name,
                           tasks=tasks,
                           variables=variables,
                           issue_types=issue_types,
                           assignees=assignees,
                           sprints=sprints,
                           order_types=order_types)


@APP.route('/add-task', methods=['POST'])
def add_task():
    max_id = 0
    for task in tasks:
        if int(task['id']) > max_id:
            max_id = int(task['id'])

    tasks.append({
        'id': max_id + 1,
        'type': request.form.get('task-type'),
        'name': request.form.get('task-name'),
        'assignee': request.form.get('task-assignee'),
        'label': request.form.get('task-label'),
        'sprint': request.form.get('task-sprint'),
        'description': request.form.get('task-description'),
        'order': request.form.get('task-order-type')
    })

    return jsonify({'success': True})


@APP.route('/remove-task', methods=['POST'])
def remove_task():
    task_id = request.form.get('task-id')

    for i in range(len(tasks)):
        if tasks[i]['id'] == int(task_id):
            tasks.pop(i)
            break

    return jsonify({'success': True})


@APP.route('/edit-task', methods=['POST'])
def edit_task():
    task_id = request.form.get('task-id')
    task_name = request.form.get('task-name')
    task_description = request.form.get('task-description')
    task_label = request.form.get('task-label')
    task_sprint = request.form.get('task-sprint')
    task_assignee = request.form.get('task-assignee')
    task_type = request.form.get('task-type')
    task_order_type = request.form.get('task-order-type')

    for i in range(len(tasks)):
        if tasks[i]['id'] == int(task_id):
            tasks[i]['name'] = task_name
            tasks[i]['description'] = task_description
            tasks[i]['label'] = task_label
            tasks[i]['sprint'] = task_sprint
            tasks[i]['assignee'] = task_assignee
            tasks[i]['type'] = task_type
            tasks[i]['order'] = task_order_type
            break

    return jsonify({'success': True})


@APP.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    for task in tasks:
        if task['id'] == int(task_id):
            return jsonify(task)

    return render_template('404.html'), 404


@APP.route('/tasks', methods=['GET'])
def get_tasks():
    tasks2 = copy.deepcopy(tasks)

    print(sprints)
    print(order_types)
    print(tasks2)
    for task in tasks2:
        for sprint in sprints:
            if int(task['sprint']) == sprint['id']:
                task['sprint'] = sprint['name']
                break
        for order_type in order_types:
            if int(task['order']) == order_type['id']:
                task['order'] = order_type['name']
                break

    print(tasks2)

    return jsonify(tasks2)


@APP.route('/raw-tasks', methods=['GET'])
def get_raw_tasks():
    return jsonify(tasks)


@APP.route('/upload-tasks', methods=['POST'])
def upload_tasks():
    file = request.files['file']
    if file:
        file_content = json.loads(file.read().decode('utf-8'))
        global tasks
        tasks = file_content
        return jsonify({'success': True})

    return jsonify({'success': False})


@APP.route('/add-variable', methods=['POST'])
def add_variable():
    for variable in variables:
        if variable['key'] == request.form.get('variable-key'):
            return jsonify({'success': False})

    max_id = 0
    for i in range(len(variables)):
        if int(variables[i]['id']) > max_id:
            max_id = int(variables[i]['id'])

    variables.append({
        'id': max_id + 1,
        'key': request.form.get('variable-key'),
        'value': request.form.get('variable-value'),
    })

    return jsonify({'success': True})


@APP.route('/remove-variable', methods=['POST'])
def remove_variable():
    variable_id = request.form.get('variable-id')

    for i in range(len(variables)):
        if variables[i]['id'] == int(variable_id):
            variables.pop(i)
            break

    return jsonify({'success': True})


@APP.route('/edit-variable', methods=['POST'])
def edit_variable():
    variable_id = request.form.get('variable-id')
    variable_key = request.form.get('variable-key')
    variable_value = request.form.get('variable-value')

    for i in range(len(variables)):
        if variables[i]['id'] == int(variable_id):
            variables[i]['key'] = variable_key
            variables[i]['value'] = variable_value
            break

    return jsonify({'success': True})


@APP.route('/variables/<variable_id>', methods=['GET'])
def get_variable(variable_id):
    for variable in variables:
        if variable['id'] == int(variable_id):
            return jsonify(variable)

    return render_template('404.html'), 404


@APP.route('/variables', methods=['GET'])
def get_variables():
    return jsonify(variables)


@APP.route('/upload-variables', methods=['POST'])
def upload_variables():
    file = request.files['file']
    if file:
        file_content = json.loads(file.read().decode('utf-8'))
        global variables
        variables = file_content
        return jsonify({'success': True})

    return jsonify({'success': False})


@APP.route('/generate', methods=['POST'])
def generate():
    # copy tasks variable into tasks_with_replaced_variables without it being a reference
    tasks_with_replaced_variables = copy.deepcopy(tasks)

    # replace variables in tasks
    for task in tasks_with_replaced_variables:
        for variable in variables:
            task['name'] = task['name'].replace('$' + variable['key'] + '$', variable['value'])
            task['description'] = task['description'].replace('$' + variable['key'] + '$', variable['value'])
            task['label'] = task['label'].replace('$' + variable['key'] + '$', variable['value'])
            task['label'] = task['label'].replace(' ', '-')

    # generate tasks
    for task in tasks_with_replaced_variables:
        print(selected_project_key)
        print(task)
        print(tasks)
        JIRA.create_issue(project=selected_project_key,
                          summary=task['name'],
                          description=task['description'],
                          issuetype={'name': task['type']},
                          assignee={'name': task['assignee']},
                          labels=[task['label']],
                          customfield_10006=int(task['sprint']),
                          customfield_12400={'id': task['order']})

    return jsonify({'success': True})


def update(project_key):
    global issue_types, assignees, sprints, order_types
    issue_types = utils.get_issue_types(JIRA, project_key)
    assignees = utils.get_assignees(JIRA, project_key)
    sprints = utils.get_sprints(JIRA, project_key)
    order_types = utils.get_order_types(JIRA, project_key)


if __name__ == '__main__':
    # APP.run(debug=True, host=CONFIG['host'], port=CONFIG['port'])
    serve(APP, host=CONFIG['host'], port=CONFIG['port'])
    