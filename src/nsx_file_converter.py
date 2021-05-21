import logging
from pathlib import Path

from alive_progress import alive_bar

import config
from sn_notebook import Notebook
from sn_note_page import NotePage
from sn_zipfile_reader import NSXZipFileReader


def what_module_is_this():
    return __name__


class NSXFile:

    def __init__(self, file, conversion_settings, pandoc_converter):
        self.logger = logging.getLogger(f'{config.APP_NAME}.{what_module_is_this()}.{self.__class__.__name__}')
        self.logger.setLevel(config.logger_level)
        self._conversion_settings = conversion_settings
        self._nsx_file_name = file
        self._zipfile_reader = NSXZipFileReader(self._nsx_file_name)
        self._nsx_json_data = ''
        self._notebook_ids = None
        self._note_page_ids = None
        self._notebooks = {}
        self._note_pages = {}
        self._note_page_count = 0
        self._note_book_count = 0
        self._image_count = 0
        self._attachment_count = 0
        self._pandoc_converter = pandoc_converter

    def process_nsx_file(self):
        self.logger.info(f"Processing {self._nsx_file_name}")
        self._nsx_json_data = self.fetch_json_data('config.json')
        self._notebook_ids = self._nsx_json_data['notebook']
        self._note_page_ids = self._nsx_json_data['note']
        self.add_notebooks()
        self.add_recycle_bin_notebook()
        self.create_export_folder_if_not_exist()
        self.create_folders()
        self.add_note_pages()
        self.add_note_pages_to_notebooks()
        self.generate_note_page_filename_and_path()
        self.process_notebooks()
        self.create_attachments()
        self.logger.info(f"Processing of {self._nsx_file_name} complete.")

    def generate_note_page_filename_and_path(self):
        for note_page in self.note_pages.values():
            # this has to happen before processing as the file name and path are needed for pre_processing content
            # and all notes have to have these set before any of them are processed to allow links between notes
            # to be created
            note_page.generate_filenames_and_paths()

    def fetch_json_data(self, data_id):
        return self._zipfile_reader.read_json_data(data_id)

    def fetch_attachment_file(self, file_name):
        return self._zipfile_reader.read_attachment_file(file_name)

    def add_notebooks(self):
        self.logger.info(f"Creating Notebooks")
        self._notebooks = {
            notebook_id: Notebook(self, notebook_id)
            for notebook_id in self._notebook_ids
        }
        self._note_book_count += len(self._notebooks)

    def add_recycle_bin_notebook(self):
        self.logger.debug(f"Creating recycle bin notebook")
        self._notebooks['recycle-bin'] = Notebook(self, 'recycle-bin')

    def create_export_folder_if_not_exist(self):
        self.logger.debug(f"Creating export folder if it does not exist")

        target_path = Path(self.conversion_settings.working_directory, config.DATA_DIR,
                           self._conversion_settings.export_folder_name)

        target_path.mkdir(exist_ok=True)
        self._conversion_settings.export_folder_name = target_path.stem

    def create_folders(self):
        self.logger.debug(f"Creating folders for notebooks")
        for notebooks_id in self._notebooks:
            self._notebooks[notebooks_id].create_folders()

    def add_note_pages(self):
        self.logger.debug(f"Creating note page objects")

        if config.silent:
            self._note_pages = {
                note_id: NotePage(self, note_id)
                for note_id in self._note_page_ids
            }
            self._note_page_count += len(self._note_pages)

            return

        print("Finding note pages")
        with alive_bar(len(self._note_page_ids), bar='blocks') as bar:
            for note_id in self._note_page_ids:
                note_page = NotePage(self, note_id)
                self._note_pages[note_id] = note_page
                bar()

            self._note_page_count += len(self._note_pages)

    def add_note_pages_to_notebooks(self):
        self.logger.info(f"Add note pages to notebooks")

        for note_page_id in self._note_pages:
            current_parent_id = self._note_pages[note_page_id].parent_notebook
            if current_parent_id in self._notebooks:
                self._notebooks[current_parent_id].add_note_page_and_set_parent_notebook(self._note_pages[note_page_id])
            else:
                self._notebooks['recycle-bin'].add_note_page_and_set_parent_notebook(self._note_pages[note_page_id])


    def create_attachments(self):
        self.logger.debug(f"Creating attachment objects")
        for note_page_id in self._note_pages:
            image_count, attachment_count = self._note_pages[note_page_id].create_attachments()
            self._image_count += image_count
            self._attachment_count += attachment_count

    def process_notebooks(self):
        for notebooks_id in self._notebooks:
            self._notebooks[notebooks_id].process_notebook_pages()

    @property
    def notebooks(self):
        return self._notebooks

    @property
    def nsx_file_name(self):
        return self._nsx_file_name

    @property
    def conversion_settings(self):
        return self._conversion_settings

    @property
    def zipfile_reader(self):
        return self._zipfile_reader


    @property
    def pandoc_converter(self):
        return self._pandoc_converter

    @property
    def note_page_count(self):
        return self._note_page_count

    @property
    def note_book_count(self):
        return self._note_book_count

    @property
    def image_count(self):
        return self._image_count

    @property
    def attachment_count(self):
        return self._attachment_count

    @property
    def note_pages(self):
        return self._note_pages
