from abc import ABC, abstractmethod
import logging
from globals import APP_NAME
import inspect


def what_module_is_this():
    return __name__


def what_method_is_this():
    return inspect.currentframe().f_back.f_code.co_name


def what_class_is_this(obj):
    return obj.__class__.__name__


class MetaDataGenerator(ABC):
    pass


class PostProcessing(ABC):
    """Abstract class representing a pre conversion note formatting """

    @abstractmethod
    def post_process_note_page(self):
        pass


class NoteStationPostProcessing(PostProcessing):
    def __init__(self, note):
        self.logger = logging.getLogger(f'{APP_NAME}.{what_module_is_this()}.{what_class_is_this(self)}')
        self.logger.setLevel(logging.DEBUG)
        self._note = note
        self._conversion_settings = note.conversion_settings
        self._yaml_header = ''
        self._post_processed_content = note.converted_content
        self._pre_processor = note.pre_processor
        self.post_process_note_page()

    def post_process_note_page(self):
        if self._conversion_settings.include_meta_data:
            self.__add_meta_data()

        self.__add_check_lists()

    def __add_meta_data(self):
        if self._note.conversion_settings.yaml_meta_header_format:
            self._post_processed_content = f'{self._pre_processor.header_generator.metadata_yaml}' \
                                           f'\n{self._post_processed_content}'
            return

        if not self._note.conversion_settings.yaml_meta_header_format:
            self._post_processed_content = f'{self._post_processed_content}' \
                                           f'\n{self._pre_processor.header_generator.metadata_text}\n'
            return

    def __add_check_lists(self):
        for checklist_item in self._pre_processor.check_list_items.values():
            search_for = f'check-list-{str(id(checklist_item))}'
            replace_with = f'{checklist_item.processed_item}  '
            self._post_processed_content = self._post_processed_content.replace(search_for, replace_with)

    @property
    def post_processed_content(self):
        return self._post_processed_content
