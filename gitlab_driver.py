# coding: utf-8
import gitlab
import requests
from fabric import colors
from repository import Repository


class GitlabRepository(Repository):

    def __init__(self, user, password, url, base_path):
        super(GitlabRepository, self).__init__(user, password, url, base_path)
        self.gitlab = gitlab.Gitlab(self.hostname)
        self.gitlab.login(self.user, self.password)

        self.gitlab_project_id = None
        i = 1
        projects = self.gitlab.getprojects(page=i, per_page=100)

        while projects and not self.gitlab_project_id:
            for project in projects:
                if project['path_with_namespace'] == "%s/%s" % (self.owner, self.name,):
                    self.gitlab_project_id = project['id']

            i += 1
            projects = self.gitlab.getprojects(page=i, per_page=100)
        if not self.gitlab_project_id:
            raise Exception("Gitlab Error", "Unable to find Gitlab repository: %s" % self.clone_url)

    def search_deployment_key(self, key_name=''):
        """
        Search a project deployment key by name
        :param key_name:
        :return: list of deploy_key ids
        """
        if not key_name:
            return []
            
        all_keys_list = self.gitlab.listdeploykeys(self.gitlab_project_id)

        if not all_keys_list:
            return []
        keys_list = filter(None, [key['id'] if key['title'] == key_name else None for key in all_keys_list])
        return keys_list

    def post_deployment_key(self, key_name, key_string):
        """
        Upload a deployment key to repo
        :param key_name: Name of the key to upload (bitbucket's label).
        :type key_name: str
        :param key_string: SSH Key
        :type key_string: str
        :return: True or False
        :rtype: boolean
        """
        return self.gitlab.adddeploykey(self.gitlab_project_id, key_name, key_string)

    def delete_deployment_key(self, key_id):
        """
        Delete deployment key
        :param key_id: a gitlab key_id
        :type key_id: int
        :return: True or False
        :rtype: boolean
        """
        result = self.gitlab.deletedeploykey(self.gitlab_project_id, key_id)
        return result

    def update_deployment_key(self, key_name, key_string):
        """
        Delete existing deployment keys named as key_name, then upload a new one
        :param key_name: Name of the key to update (bitbucket's label).
        :type key_name: str
        :param key_string: SSH Key
        :type key_string: str
        :return: True or False
        :rtype: boolean
        """
        # for update, we don't bother if key do not exists
        keys = self.search_deployment_key(key_name)
        for key in keys:
            self.delete_deployment_key(key)
        return self.post_deployment_key(key_name, key_string)

    @property
    def clone_command_line(self):
        if self.dvcs == 'hg':
            if self.version:
                return "hg clone -y -r %s %s %s" % (self.version, self.clone_url, self.destination_directory,)
            return "hg clone -y %s %s" % (self.clone_url, self.destination_directory,)

        # elif self.dvcs == 'git':
        return "git clone %s %s" % (self.clone_url, self.destination_directory,)

    @property
    def checkout_command_line(self):
        if not self.version:
            return ''
        if self.dvcs == 'hg':
            return "hg update %s" % (self.version,)
        # elif self.dvcs == 'git':
        return "git checkout %s" % (self.version,)

    @property
    def pull_command_line(self):
        if self.dvcs == 'hg':
            return "hg pull -u'"
        # elif self.dvcs == 'git':
        return "git pull origin master"

