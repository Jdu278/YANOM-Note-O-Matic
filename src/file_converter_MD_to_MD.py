from file_converter_abstract import FileConverter
from metadata_processing import MetaDataProcessor


class MDToMDConverter(FileConverter):
    def pre_process_content(self):
        self._pre_processed_content = self._file_content
        self.parse_metadata_if_required()
        self.pre_process_obsidian_image_links_if_required()
        self.rename_target_file_if_it_already_exists()

    def parse_metadata_if_required(self):
        self._metadata_processor = MetaDataProcessor(self._conversion_settings)
        self._pre_processed_content = self._metadata_processor.parse_md_metadata(self._pre_processed_content)

    def post_process_content(self):
        self._post_processed_content = self._pre_processed_content
        self.post_process_obsidian_image_links_if_required()
        self.add_meta_data_if_required()
        self._post_processed_content = self.handle_attachment_paths(self._post_processed_content)

    def add_meta_data_if_required(self):
        self._post_processed_content = self._metadata_processor.add_metadata_md_to_content(self._post_processed_content)
