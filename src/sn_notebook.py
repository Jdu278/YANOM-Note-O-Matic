import inspect
import logging
from pathlib import Path

from globals import APP_NAME, DATA_DIR
from helper_functions import generate_clean_path, find_working_directory
from sn_note_page import NotePage


def what_module_is_this():
    return __name__


def what_method_is_this():
    return inspect.currentframe().f_back.f_code.co_name


def what_class_is_this(obj):
    return obj.__class__.__name__


class Notebook:
    def __init__(self, nsx_file, notebook_id):
        self.logger = logging.getLogger(f'{APP_NAME}.{what_module_is_this()}.{what_class_is_this(self)}')
        self.logger.setLevel(logging.DEBUG)
        self.nsx_file = nsx_file
        self.notebook_id = notebook_id
        self.conversion_settings = self.nsx_file.conversion_settings
        self.notebook_json = dict
        if self.notebook_id == 'recycle_bin':
            self.title = 'recycle_bin'
        if self.notebook_id != 'recycle_bin':
            self.fetch_notebook_data()
            self.title = self.notebook_json['title']
        self.folder_name = ''
        self.create_folder_name()
        self.full_path_to_notebook = ''
        self.note_pages = []
        self.note_titles = []

    def fetch_notebook_data(self):
        self.notebook_json = self.nsx_file.zipfile_reader.read_json_data(self.notebook_id)
        if self.notebook_json['title'] == "":  # The notebook with no title is called 'My Notes' in note station
            self.notebook_json['title'] = "My Notebook"

    def process_notebook_pages(self):
        self.logger.info(f"Processing note book {self.title} - {self.notebook_id}")

        for note_page in self.note_pages:
            note_page.process_note()

    def add_note_page_and_set_parent_notebook(self, note_page: NotePage):
        self.logger.info(f"Adding note '{note_page.title}' - {note_page.note_id} "
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
        self.logger.info(f"Creating notebook folder for {self.title}")
        current_directory_path, message = find_working_directory()
        self.logger.info(message)

        n = 0
        target_path = Path(current_directory_path, DATA_DIR,
                           self.nsx_file.conversion_settings.export_folder_name,
                           self.folder_name)

        while target_path.exists():
            n += 1
            target_path = Path(current_directory_path, DATA_DIR,
                               self.nsx_file.conversion_settings.export_folder_name,
                               f"{self.folder_name}-{n}")

        target_path.mkdir(parents=True, exist_ok=True)
        self.folder_name = target_path.stem
        self.full_path_to_notebook = target_path

    def create_attachment_folder(self):
        self.logger.info(f"Creating attachment")
        Path(self.full_path_to_notebook, self.conversion_settings.attachment_folder_name).mkdir()
