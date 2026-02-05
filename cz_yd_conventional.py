import os
import re

from commitizen import defaults
from commitizen.cz.base import BaseCommitizen
from commitizen.cz.utils import multiple_line_breaker, required_validator
from commitizen.defaults import Questions

# Export the YDConventional class for external use
__all__ = ['YDConventional']

class YDConventional(BaseCommitizen):
    # Mapping for version bumping behavior, depending on the commit type
    bump_map = defaults.bump_map
    bump_map_major_version_zero = defaults.bump_map_major_version_zero
    bump_pattern = defaults.bump_pattern # Pattern for parsing commits to identify version bumps

    # Regex for parsing the commit message, capturing change type, scope, breaking changes, and the message body
    commit_parser = r'^((?P<change_type>feat|fix|refactor|perf|BREAKING CHANGE)(?:\((?P<scope>[^()\r\n]*)\)|\()?(?P<breaking>!)?|\w+!):\s(?P<message>.*)?'  # noqa

    # The pattern to match the changes for changelogs
    changelog_pattern = defaults.bump_pattern

    # Mapping of common change types to more readable formats
    change_type_map = {
        'feat': 'Feat',
        'fix': 'Fix',
        'refactor': 'Refactor',
        'perf': 'Perf'
    }

    # Regex pattern for matching the issue ID format (e.g., YD-1234)
    issue_pattern = r'([Yy][Dd]-\d+)'

    def parse_scope(self, text: str) -> str:
        """
        Parse and format the scope of the commit message.

        If the scope matches an issue ID (e.g., YD-1234), it ensures the 'ref' prefix is added.
        Otherwise, it formats the scope by joining words with hyphens.
        """
        if not text:
            return ''

        scope = text.strip() # Remove any surrounding whitespace
        match = re.search(self.issue_pattern, scope)

        if match:
            # If scope already starts with "ref ", return it as-is
            if scope.startswith('ref '):
                return scope
            else:
                # Add the "ref " prefix if not present
                return f'ref {match.group(0)}'

        # If no issue pattern is found, join words with hyphens
        return '-'.join(scope.split())

    def parse_subject(self, text: str) -> str:
        """
        Parse and validate the commit message subject.

        Ensures the subject is required and does not have a trailing period.
        """
        if isinstance(text, str):
            text = text.strip('.').strip() # Remove trailing period and whitespace

        return required_validator(text, msg='Subject is required') # Ensure subject is not empty


    def read_issue_id_from_branch(self, answers = None) -> str:
        """
        Automatically read the issue ID from the current Git branch name.

        This is used as the default scope if an issue ID (e.g., YD-1234) is present in the branch name.
        """
        command = 'git branch --show-current'  # Command to get the current branch name

        # Open a subprocess to execute the Git command
        with os.popen(command) as proc:
            branch_name = proc.read().strip() # Get the branch name and remove surrounding whitespace
            match = re.search(self.issue_pattern, branch_name)

            if match:
                # If an issue ID is found in the branch name, return it formatted as scope
                issue_id = self.parse_scope(match.group(0))
                return issue_id

        return ''  # Return an empty string if no issue ID is found

    def questions(self) -> Questions:
        """
        Define the prompts that will be asked during the commit message creation process.

        This includes selecting the commit type, scope, subject, body, breaking change confirmation, and footer.
        """

        # Prompt for the type of commit being made
        commit_type = {
            'type': 'list',
            'name': 'commit_type',
            'message': 'Select the type of change you are committing',
            'choices': [
                {
                    'value': 'chore',
                    'name': 'chore: A change that has no impact on performance and doesn\'t represent a feature or fix',
                    'key': 'h',
                },
                {
                    'value': 'fix', # correlates with PATCH in SemVer
                    'name': 'fix: A bug fix',
                    'key': 'x',
                },
                {
                    'value': 'feat', # correlates with MINOR in SemVer
                    'name': 'feat: A new feature',
                    'key': 'f',
                },
                {
                    'value': 'docs',
                    'name': 'docs: Documentation only changes',
                    'key': 'd',
                },
                {
                    'value': 'style',
                    'name': (
                        'style: Changes that do not affect the '
                        'meaning of the code (white-space, formatting,'
                        ' missing semi-colons, etc)'
                    ),
                    'key': 's',
                },
                {
                    'value': 'refactor', # correlates with PATCH in SemVer
                    'name': (
                        'refactor: A code change that neither fixes '
                        'a bug nor adds a feature'
                    ),
                    'key': 'r',
                },
                {
                    'value': 'perf', # correlates with PATCH in SemVer
                    'name': 'perf: A code change that improves performance',
                    'key': 'p',
                },
                {
                    'value': 'test',
                    'name': 'test: Adding missing or correcting ' 'existing tests',
                    'key': 't',
                },
                {
                    'value': 'build',
                    'name': (
                        'build: Changes that affect the build system or '
                        'external dependencies (example scopes: pip, docker, npm)'
                    ),
                    'key': 'b',
                },
                {
                    'value': 'ci',
                    'name': (
                        'ci: Changes to CI configuration files and '
                        'scripts'
                    ),
                    'key': 'c',
                },
                {
                    'value': 'wip',
                    'name': 'wip: Work in progress',
                    'key': 'w',
                },
            ],
        }

        # Prompt for the scope of the commit (e.g., issue ID or module name)
        commit_scope = {
            'type': 'input',
            'name': 'commit_scope',
            'message': 'What is the scope of this change? (linear issue-id)\n',
            'filter': self.parse_scope,  # Automatically format the scope
            'default': self.read_issue_id_from_branch,  # Default to reading the issue ID from the branch name
        }

        # Prompt for the subject of the commit (a short, imperative summary)
        commit_subject = {
            'type': 'input',
            'name': 'commit_subject',
            'message': 'Write a short and imperative summary of the code changes: (lower case and no period)\n',
            'filter': self.parse_subject,  # Automatically format and validate the subject
        }

        # Prompt for the commit body (optional, allows for multiline input)
        commit_body = {
            'type': 'input',
            'name': 'commit_body',
            'message': 'Provide additional contextual information about the code changes: (press [enter] to skip)\n',
            'filter': multiple_line_breaker,  # Format the body for multi-line input
        }

        # Confirm if the commit includes a breaking change
        commit_breaking_change = {
            'type': 'confirm',
            'name': 'commit_breaking', # correlates with MAJOR in SemVer
            'message': 'Is this a BREAKING CHANGE?\n',
            'default': False,
        }

        # Prompt for additional footer information (e.g., reference issues or breaking change details)
        commit_footer = {
            'type': 'input',
            'name': 'commit_footer', # correlates with MAJOR in SemVer
            'message': (
                'Information about Breaking Changes or '
                'reference additional linear tickets (ref [ISSUE-ID]): (press [enter] to skip)\n'
            ),
        }

        # Return all the prompts to be displayed in the commit message flow
        return [
            commit_type,
            commit_scope,
            commit_subject,
            commit_body,
            commit_breaking_change,
            commit_footer
        ]

    def message(self, answers: dict) -> str:
        """
        Generate the final commit message based on the user's answers to the prompts.
        This method formats the commit message according to the conventional commit structure.
        """
        commit_type = answers['commit_type']
        scope = answers['commit_scope']
        subject = answers['commit_subject']
        body = answers['commit_body']
        footer = answers['commit_footer']
        is_breaking_change = answers['commit_breaking']

        if scope:
            scope = f'({scope})'
        if body:
            body = f'\n\n{body}'
        if is_breaking_change:
            footer = f'BREAKING CHANGE: {footer}'
        if footer:
            footer = f'\n\n{footer}'

        # Return the formatted commit message
        message = f'{commit_type}{scope}: {subject}{body}{footer}'

        return message

    def example(self) -> str:
        """Provide an example of a properly formatted commit message following this convention."""
        return (
            'fix(ref YD-2000): correct minor typos in code\n'
            '\n'
            'see the issue for details on the typos fixed\n'
            '\n'
            'ref YD-2012'
        )

    def schema(self) -> str:
        """Return the commit message schema that this implementation enforces."""
        return (
            '<type>(<scope>): <subject>\n'
            '<BLANK LINE>\n'
            '<body>\n'
            '<BLANK LINE>\n'
            '(BREAKING CHANGE: )<footer>'
        )

    def schema_pattern(self) -> str:
        """Define the regex pattern that is used to validate the commit message format."""
        PATTERN = (
            r'(?s)'  # To explicitly make . match new line
            r'(build|ci|docs|feat|fix|perf|refactor|style|test|chore|revert|bump|wip)'  # type
            r'(\(\S+\))?!?:'  # scope
            r'( [^\n\r]+)'  # subject
            r'((\n\n.*)|(\s*))?$'
        )
        return PATTERN

    def info(self) -> str:
        """
        Return additional information from an external text file.
        This is typically used to display more context about the commit convention.
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        filepath = os.path.join(dir_path, 'cz_yd_conventional.txt')
        with open(filepath, encoding=self.config.settings['encoding']) as f:
            content = f.read()
        return content

    def process_commit(self, commit: str) -> str:
        """
        Process a given commit message to extract the subject using the schema pattern.

        This method is used to validate and process the commit message.
        """
        pat = re.compile(self.schema_pattern())
        m = re.match(pat, commit)
        if m is None:
            return ''
        return m.group(3).strip()

    def run(self, *args):
        """Main entry point for the CLI commands."""
        if 'info' in args:
            print(self.info())
        else:
            # handle other commands or fallbacks
            print("Unknown command. Use 'info' for commit info.")
