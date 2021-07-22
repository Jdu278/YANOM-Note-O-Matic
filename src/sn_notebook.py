import logging
from pathlib import Path

from alive_progress import alive_bar

import config
from helper_functions import generate_clean_path, find_working_directory
from sn_note_page import NotePage


def what_module_is_this():
    return __name__


class Notebook:
    def __init__(self, nsx_file, notebook_id, title):
        self.logger = logging.getLogger(f'{config.APP_NAME}.{what_module_is_this()}.{self.__class__.__name__}')
        self.logger.setLevel(config.logger_level)
        self.nsx_file = nsx_file
        self.notebook_id = notebook_id
        self.conversion_settings = self.nsx_file.conversion_settings
        self.notebook_json = dict
        self.title = title
        self.folder_name = ''
        self.create_folder_name()
        self.full_path_to_notebook = ''
        self.note_pages = []
        self.note_titles = []

    def process_notebook_pages(self):
        self.logger.info(f"Processing note book {self.title} - {self.notebook_id}")

        if not config.silent:
            print(f"Processing '{self.title}' Notebook")
        with alive_bar(len(self.note_pages), bar='blocks') as bar:
            for note_page in self.note_pages:
                note_page.process_note()
                if not config.silent:
                    bar()

    def pair_up_note_pages_and_notebooks(self, note_page: NotePage):
        self.logger.debug(f"Adding note '{note_page.title}' - {note_page.note_id} "
                          f"to Notebook '{self.title}' - {self.notebook_id}")

        note_page.notebook_folder_name = self.folder_name
        note_page.parent_notebook = self.notebook_id

        while note_page.title in self.note_titles:
            note_page.increment_duplicated_title(self.note_titles)

        self.note_titles.append(note_page.title)
        self.note_pages.append(note_page)

    def create_folder_name(self):
        self.folder_name = generate_clean_path(self.title)

    def create_folders(self):
        self.create_notebook_folder()
        self.create_attachment_folder()

    def create_notebook_folder(self):
        self.logger.debug(f"Creating notebook folder for {self.title}")
        current_directory_path = self.conversion_settings.working_directory

        n = 0
        target_path = Path(current_directory_path, config.DATA_DIR,
                           self.nsx_file.conversion_settings.export_folder_name,
                           self.folder_name)

        while target_path.exists():
            n += 1
            target_path = Path(current_directory_path, config.DATA_DIR,
                               self.nsx_file.conversion_settings.export_folder_name,
                               f"{self.folder_name}-{n}")

        target_path.mkdir(parents=True, exist_ok=True)
        self.folder_name = target_path.name
        self.full_path_to_notebook = target_path

    def create_attachment_folder(self):
        self.logger.debug(f"Creating attachment folder")
        Path(self.full_path_to_notebook, self.conversion_settings.attachment_folder_name).mkdir()
