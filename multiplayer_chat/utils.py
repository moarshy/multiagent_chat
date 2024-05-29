class Workflow:
    def __init__(self, name, workflow_config):
        self.name = name
        self.workflow_config = workflow_config
        self.tasks = []

    def add_task(self, node, task_name, *args):
        self.tasks.append((node, task_name, args))