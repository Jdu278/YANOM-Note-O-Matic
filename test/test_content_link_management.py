import os
from pathlib import Path

import pytest

import content_link_management
from content_link_management import get_attachment_paths, update_content_with_new_paths
from conversion_settings import ConversionSettings
from file_converter_HTML_to_MD import HTMLToMDConverter
import helper_functions


def test_absolute_path_from_relative_path(tmp_path):
    file_path = Path(tmp_path, 'some_folder/another_folder/file.txt')
    link = Path('../a_different_folder/the_file.txt')

    expected = Path(tmp_path, 'some_folder/a_different_folder/the_file.txt')

    result = content_link_management.absolute_path_from_relative_path(file_path, link)

    assert result == expected


def test_calculate_relative_path(tmp_path):
    target_root = Path(tmp_path, 'some_folder/another_folder')
    absolute_link = Path(tmp_path, 'some_other_folder/another_folder/file.txt')

    expected = Path('../../some_other_folder/another_folder/file.txt')

    result = content_link_management.calculate_relative_path(absolute_link, target_root)

    assert result == expected


def test_update_content_with_new_link():
    content = '![non-copyable](../../attachments/four.csv)\n'
    expected = '![non-copyable](../attachments/four.csv)\n'
    old_path = Path('../../attachments/four.csv')
    new_path = Path('../attachments/four.csv')
    result = content_link_management.update_content_with_new_link(old_path, new_path, content)

    assert result == expected


def test_update_href_link_suffix_in_content():
    content = '<a href="attachments/eleven.pdf">example-attachment</a>'
    output_suffix = '.md'
    links_to_update = [Path('attachments/eleven.pdf')]
    expected = '<a href="attachments/eleven.md">example-attachment</a>'

    result = content_link_management.update_href_link_suffix_in_content(content, output_suffix, links_to_update)

    assert result == expected


def test_update_href_link_suffix_in_content_no_matching_path_on_links_to_update():
    content = '<a href="attachments/eleven.pdf">example-attachment</a>'
    output_suffix = '.md'
    links_to_update = [Path('attachments/twelve.pdf')]
    expected = '<a href="attachments/eleven.pdf">example-attachment</a>'

    result = content_link_management.update_href_link_suffix_in_content(content, output_suffix, links_to_update)

    assert result == expected


def test_update_href_link_suffix_in_content_no_href_in_content():
    content = 'example-attachment'
    output_suffix = '.md'
    links_to_update = [Path('attachments/twelve.pdf')]
    expected = 'example-attachment'

    result = content_link_management.update_href_link_suffix_in_content(content, output_suffix, links_to_update)

    assert result == expected


def test_update_relative_links_to_absolute_links(tmp_path):
    content_file_path = Path(tmp_path, 'some_folder/folder1/file.txt')
    link_set = {
        Path('../folder2/file2.txt'),
        Path(tmp_path, 'some_folder/folder3/file3.txt')
    }

    expected = {
        Path(tmp_path, 'some_folder/folder2/file2.txt'),
        Path(tmp_path, 'some_folder/folder3/file3.txt')
    }

    result = content_link_management.update_relative_links_to_absolute_links(content_file_path, link_set)

    assert result == expected


def test_set_of_html_href_file_paths_from():
    content = f'<img src="attachments/ten.png" />\n' \
              f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
              f'![copyable](attachments/file%20twelve.pdf)\n' \
              f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
              f'<img src="attachments/file%20fourteen.png" />\n' \
              f'<a href="mailto:person@exmaple.com">person@exmaple.com</a>\n' \
              f'<a href="tel:123456">person@exmaple.com</a>\n' \
              f'<a href="https://www.google.com">person@exmaple.com</a>\n' \
              f'<a href="http://www.google.com">person@exmaple.com</a>'
    expected = {
        'attachments/eleven.pdf',
        'attachments/file thirteen.pdf'
    }
    result = content_link_management.set_of_html_href_file_paths_from(content)

    assert result == expected


def test_set_of_html_img_file_paths_from():
    content = f'<img src="attachments/ten.png" />\n' \
              f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
              f'![copyable](attachments/file%20twelve.pdf)\n' \
              f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
              f'<img src="attachments/file%20fourteen.png" />' \
              f'<img src="https://www.dummy.com/image.png" />' \
              f'<img src="http://www.dummy.com/image2.png" />'
    expected = {
        'attachments/ten.png',
        'attachments/file fourteen.png'
    }
    result = content_link_management.set_of_html_img_file_paths_from(content)

    assert result == expected


def test_set_of_markdown_file_paths_from():
    content = f'![copyable](../my_other_notebook/attachments/five.pdf "test tool tip text")\n' \
              f'![note link](nine.md)\n' \
              f'[a web link](https://www.google.com "google")\n' \
              f'<img src="attachments/ten.png" />\n' \
              f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
              f'![copyable](attachments/file%20twelve.pdf)\n' \
              f'![a web link](https://www.dummy.com/file1/txt)\n' \
              f'![a web link](http://www.dummy.com/file2/txt)\n' \
              f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
              f'<img src="attachments/file%20fourteen.png" />'
    expected = {
        '../my_other_notebook/attachments/five.pdf',
        'nine.md',
        'attachments/file twelve.pdf'
    }

    result = content_link_management.set_of_markdown_file_paths_from(content)

    assert result == expected


@pytest.mark.parametrize(
    'file_type, expected', [
        ('html', {
            'attachments/ten.png',
            'attachments/eleven.pdf',
            'attachments/file thirteen.pdf',
            'attachments/file fourteen.png',
        },
        ),
        ('markdown', {
            'attachments/ten.png',
            'attachments/eleven.pdf',
            'attachments/file twelve.pdf',
            'attachments/file thirteen.pdf',
            'attachments/file fourteen.png',
        },
        ),
    ]
)
def test_find_local_file_links_in_content_html(file_type, expected):
    content = f'<img src="attachments/ten.png" />\n' \
              f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
              f'![copyable](attachments/file%20twelve.pdf)\n' \
              f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
              f'<img src="attachments/file%20fourteen.png" />'

    result = content_link_management.find_local_file_links_in_content(file_type, content)

    assert result == expected


def test_scan_html_content_for_all_links():
    content = f'<img src="attachments/ten.png" />\n' \
              f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
              f'![copyable](attachments/file%20twelve.pdf)\n' \
              f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
              f'<img src="attachments/file%20fourteen.png" />'
    expected = {
        'attachments/ten.png',
        'attachments/file fourteen.png',
        'attachments/eleven.pdf',
        'attachments/file thirteen.pdf'
    }
    result = content_link_management.scan_html_content_for_all_paths(content)

    assert result == expected


def test_scan_markdown_content_for_all_links():
    content = f'![copyable](../my_other_notebook/attachments/five.pdf "test tool tip text")\n' \
              f'![note link](nine.md)\n' \
              f'[a web link](https://www.google.com "google")\n' \
              f'<img src="attachments/ten.png" />\n' \
              f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
              f'![copyable](attachments/file%20twelve.pdf)\n' \
              f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
              f'<img src="attachments/file%20fourteen.png" />'
    expected = {
        '../my_other_notebook/attachments/five.pdf',
        'nine.md',
        'attachments/file twelve.pdf',
        'attachments/ten.png',
        'attachments/file fourteen.png',
        'attachments/eleven.pdf',
        'attachments/file thirteen.pdf'
    }

    result = content_link_management.scan_markdown_content_for_all_paths(content)

    assert result == expected


def test_remove_content_links_from_links(tmp_path):
    content_file_path = Path(tmp_path, 'some_folder/folder1/file.txt')
    links = {
        '../folder2/file2.txt',
        f'{tmp_path}/some_folder/folder3/file3.txt',
        f'{tmp_path}/some_folder/content.md',
    }
    content_links = {Path(tmp_path, 'some_folder/content.md')}

    expected = {
        '../folder2/file2.txt',
        f'{tmp_path}/some_folder/folder3/file3.txt',
    }

    result = content_link_management.remove_content_links_from_links(content_file_path, content_links, links)

    assert result == expected


def test_split_set_existing_non_existing_links(tmp_path):
    content_file_path = Path(tmp_path, 'some_folder/folder1/file.txt')
    links = {
        '../folder1/file1.txt',
        '../folder2/file2.txt',
        f'{tmp_path}/some_folder/folder3/file3.txt',
        f'{tmp_path}/some_folder/Stuck on the Past - A Primer on Value Migration & How to Avoid It.pdf'
    }

    Path(tmp_path, 'some_folder/folder1').mkdir(parents=True)
    Path(tmp_path, 'some_folder/folder1/file1.txt').touch()
    Path(tmp_path, 'some_folder/folder3').mkdir(parents=True)
    Path(tmp_path, 'some_folder/folder3/file3.txt').touch()
    Path(tmp_path, 'some_folder').mkdir(exist_ok=True)
    Path(tmp_path, 'some_folder/Stuck on the Past - A Primer on Value Migration & How to Avoid It.pdf').touch()

    result = content_link_management.split_set_existing_non_existing_links(content_file_path, links)

    assert result.non_existing == {'../folder2/file2.txt'}
    assert result.existing == {
        f'{tmp_path}/some_folder/folder3/file3.txt',
        '../folder1/file1.txt',
        f'{tmp_path}/some_folder/Stuck on the Past - A Primer on Value Migration & How to Avoid It.pdf'
    }


def test_split_existing_links_copyable_non_copyable(tmp_path):
    content_file_path = Path(tmp_path, 'some_folder/folder1/file1.txt')
    root_for_copyable_paths = Path(tmp_path, 'some_folder/folder1')
    links_to_split = {
        f'{tmp_path}/some_folder/folder1/folder1-2/copyable.txt',
        'folder1-2/copyable2.txt',
        f'{tmp_path}/some_folder/folder2/folder2-2/non-copyable.txt',
        '../folder2/folder2-2/non-copyable2.txt',
    }

    result = content_link_management.split_existing_links_copyable_non_copyable(content_file_path,
                                                                                root_for_copyable_paths,
                                                                                links_to_split)

    expected_copyable = {
        f'{tmp_path}/some_folder/folder1/folder1-2/copyable.txt',
        'folder1-2/copyable2.txt',
    }

    expected_non_copyable_relative = {
        '../folder2/folder2-2/non-copyable2.txt',
    }

    expected_non_copyable_absolute = {
        f'{tmp_path}/some_folder/folder2/folder2-2/non-copyable.txt',
    }

    assert result.copyable == expected_copyable

    assert result.non_copyable_relative == expected_non_copyable_relative

    assert result.non_copyable_absolute == expected_non_copyable_absolute


def test_update_content_with_new_paths_absolute_false(tmp_path):
    content = f'![something](../attachments/five.pdf "test tool tip text")\n![something]({tmp_path}/attachments/one.pdf "test tool tip text")'
    content_file_path = Path(tmp_path, 'some_folder/file1.txt')
    path_set = {'attachments/five.pdf'}
    make_absolute = False
    root_for_absolute_paths = Path(tmp_path, 'some_folder/folder3')

    expected = f'![something](../attachments/five.pdf "test tool tip text")\n![something]({tmp_path}/attachments/one.pdf "test tool tip text")'

    result = content_link_management.update_content_with_new_paths(content,
                                                                   content_file_path,
                                                                   path_set,
                                                                   make_absolute,
                                                                   root_for_absolute_paths)

    assert result == expected


def test_update_content_with_new_paths_absolute_true(tmp_path):
    content = f'![something](../attachments/five.pdf)\n![something]({tmp_path}/attachments/one.pdf)'
    content_file_path = Path(tmp_path, 'some_folder/file1.txt')
    path_set = {
        '../attachments/five.pdf',
        f'{tmp_path}/attachments/one.pdf'
    }
    make_absolute = True
    root_for_absolute_paths = Path(tmp_path, 'some_folder/folder3')

    expected = f'![something]({helper_functions.path_to_posix_str(tmp_path)}/attachments/five.pdf)\n![something]({tmp_path}/attachments/one.pdf)'

    result = content_link_management.update_content_with_new_paths(content,
                                                                   content_file_path,
                                                                   path_set,
                                                                   make_absolute,
                                                                   root_for_absolute_paths)

    assert result == expected


def test_split_existing_links_copyable_non_copyable2_posix_file_system():
    if os.name == 'nt':
        return

    source_absolute_root = Path('/Users/user/PycharmProjects/YANOM-Note-O-Matic/src/data/notes_big')
    link_set = {Path('/Users/user/PycharmProjects/YANOM-Note-O-Matic/src/data/notes_big/portsmouth/attachments/298991566137280954.png')}
    file = Path('/Users/user/PycharmProjects/YANOM-Note-O-Matic/src/data/notes_big/portsmouth/process-capability-geotsch.md')

    results = content_link_management.split_existing_links_copyable_non_copyable(file, source_absolute_root, link_set)

    assert results.copyable == {Path('/Users/user/PycharmProjects/YANOM-Note-O-Matic/src/data/notes_big/portsmouth/attachments/298991566137280954.png')}
    assert len(results.non_copyable_relative) == 0
    assert len(results.non_copyable_absolute) == 0


def test_split_existing_links_copyable_non_copyable2_windows_file_system():
    if not os.name == 'nt':
        return

    source_absolute_root = Path('c:/Users/user/PycharmProjects/YANOM-Note-O-Matic/src/data/notes_big')
    link_set = {Path(
        'c:/Users/user/PycharmProjects/YANOM-Note-O-Matic/src/data/notes_big/portsmouth/attachments/298991566137280954.png')}
    file = Path(
        'c:/Users/user/PycharmProjects/YANOM-Note-O-Matic/src/data/notes_big/portsmouth/process-capability-geotsch.md')

    results = content_link_management.split_existing_links_copyable_non_copyable(file, source_absolute_root, link_set)

    assert results.copyable == {Path(
        'c:/Users/user/PycharmProjects/YANOM-Note-O-Matic/src/data/notes_big/portsmouth/attachments/298991566137280954.png')}
    assert len(results.non_copyable_relative) == 0
    assert len(results.non_copyable_absolute) == 0


def test_update_content_with_new_paths_for_non_movable_attachments(tmp_path):
    Path(tmp_path, 'some_folder/data/my_notebook/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/my_notebook/note.md').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/one.png').touch()
    Path(tmp_path, 'some_folder/data/attachments/two.csv').touch()
    Path(tmp_path, 'some_folder/three.png').touch()
    Path(tmp_path, 'some_folder/attachments/four.csv').touch()
    Path(tmp_path, 'some_folder/four.csv').touch()
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments/five.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/six.csv').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eight.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/nine.md').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/ten.png').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eleven.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file fourteen.png').touch()

    file_path = Path(tmp_path, 'some_folder/data/my_notebook/note.md')
    content = f'![copyable|600]({helper_functions.path_to_posix_str(tmp_path)}/some_folder/data/my_notebook/attachments/one.png)\n' \
              f'![non-existing|600]({helper_functions.path_to_posix_str(tmp_path)}/some_folder/two.png)\n' \
              f'![non-copyable|600]({helper_functions.path_to_posix_str(tmp_path)}/some_folder/three.png)\n' \
              f'![non-copyable|600](../../three.png)\n' \
              f'![non-existing|600](attachments/three.pdf)\n' \
              f'![copyable|600](attachments/eight.pdf)\n' \
              f'![copyable](../attachments/two.csv)\n' \
              f'![non-copyable](../../attachments/four.csv)\n' \
              f'![non-existing](../my_notebook/seven.csv)\n' \
              f'![copyable](../my_notebook/six.csv)\n' \
              f'![copyable](../my_other_notebook/attachments/five.pdf "test tool tip text")\n' \
              f'![note link](nine.md)\n' \
              f'[a web link](https://www.google.com)\n' \
              f'<img src="attachments/ten.png" />\n' \
              f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
              f'![copyable](attachments/file%20twelve.pdf)\n' \
              f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
              f'<img src="attachments/file%20fourteen.png" />\n' \
              f'<a href="https://www.google.com">google</a>)\n' \
              f'![]()\n' \
              f'<img src="" />\n' \
              f'<a href="">empty href link</a>'

    expected_content = f'![copyable|600]({helper_functions.path_to_posix_str(tmp_path)}/some_folder/data/my_notebook/attachments/one.png)\n' \
                       f'![non-existing|600]({helper_functions.path_to_posix_str(tmp_path)}/some_folder/two.png)\n' \
                       f'![non-copyable|600]({helper_functions.path_to_posix_str(tmp_path)}/some_folder/three.png)\n' \
                       f'![non-copyable|600]({helper_functions.path_to_posix_str(tmp_path)}/some_folder/three.png)\n' \
                       f'![non-existing|600](attachments/three.pdf)\n' \
                       f'![copyable|600](attachments/eight.pdf)\n' \
                       f'![copyable](../attachments/two.csv)\n' \
                       f'![non-copyable]({str(tmp_path.as_posix())}/some_folder/attachments/four.csv)\n' \
                       f'![non-existing](../my_notebook/seven.csv)\n' \
                       f'![copyable](../my_notebook/six.csv)\n' \
                       f'![copyable](../my_other_notebook/attachments/five.pdf "test tool tip text")\n' \
                       f'![note link](nine.md)\n' \
                       f'[a web link](https://www.google.com)\n' \
                       f'<img src="attachments/ten.png"/>\n' \
                       f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
                       f'![copyable](attachments/file%20twelve.pdf)\n' \
                       f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
                       f'<img src="attachments/file%20fourteen.png"/>\n' \
                       f'<a href="https://www.google.com">google</a>)\n' \
                       f'![]()\n' \
                       f'<img src=""/>\n' \
                       f'<a href="">empty href link</a>'

    conversion_settings = ConversionSettings()
    conversion_settings.source = Path(tmp_path, 'some_folder/data')
    conversion_settings.export_folder = Path(tmp_path, 'some_folder/export')
    conversion_settings.export_format = 'obsidian'
    conversion_settings.conversion_input = 'markdown'
    conversion_settings.make_absolute = True
    file_converter = HTMLToMDConverter(conversion_settings, 'files_to_convert')
    file_converter._file = file_path
    file_converter._files_to_convert = {Path(tmp_path, 'some_folder/data/my_notebook/nine.md')}
    attachment_links = get_attachment_paths(file_converter._conversion_settings.source_absolute_root,
                                            file_converter._conversion_settings.export_format,
                                            file_converter._file,
                                            file_converter._files_to_convert, content)
    result_content = update_content_with_new_paths(content,
                                                   file_converter._file,
                                                   attachment_links.non_copyable_relative,
                                                   file_converter._conversion_settings.make_absolute,
                                                   file_converter._conversion_settings.export_folder_absolute,
                                                   )

    assert result_content == expected_content


def test_update_markdown_link_src():
    content = "![not changed](attachments/not-changed.html)\n[should change](changed.md)\n![not changed](attachments/not-changed.html)\n[should not change](attachments/changed.md)\n![should not changed](https://changed.md)"
    old = "changed.md"
    new = Path("changed-old-1.md")
    expected = "![not changed](attachments/not-changed.html)\n[should change](changed-old-1.md)\n![not changed](attachments/not-changed.html)\n[should not change](attachments/changed.md)\n![should not changed](https://changed.md)"

    result = content_link_management.update_markdown_link_src(content, old, new)

    assert result == expected


def test_update_markdown_link_src_content_has_no_tags():
    content = "Hello world"
    old = "changed.md"
    new = Path("changed-old-1.md")
    expected = "Hello world"

    result = content_link_management.update_markdown_link_src(content, old, new)

    assert result == expected


def test_update_html_link_src():
    content = '<a href="attachments/not-changed.html">example-attachment</a><a href="attachments/changed.md">should change</a><a href="http://attachments/changed.md">should not change</a><a href="not-changed.html">example-attachment</a><a href="http://changed.md">should not change</a>'
    old = "attachments/changed.md"
    new = Path("attachments/changed-old-1.md")
    expected = '<a href="attachments/not-changed.html">example-attachment</a><a href="attachments/changed-old-1.md">should change</a><a href="http://attachments/changed.md">should not change</a><a href="not-changed.html">example-attachment</a><a href="http://changed.md">should not change</a>'

    result = content_link_management.update_html_link_src(content, old, new)

    assert result == expected


def test_split_valid_and_invalid_link_paths_windows():
    if not os.name == 'nt':
        return

    all_attachments = {
        '/hello/dog\0/cat',
        'file:///K:/SPSS%20info/',
        'c:/SPSS%20inf',
        r'attachments\example_file.pdf',
        'c:\\windows',
    }

    expected_invalid = {
        '/hello/dog\0/cat',
        'file:///K:/SPSS%20info/',
    }

    expected_valid = {
        'c:/SPSS%20inf',
        r'attachments\example_file.pdf',
        'c:\\windows',
    }

    result = content_link_management.split_valid_and_invalid_link_paths(all_attachments)

    assert result.invalid == expected_invalid

    assert result.valid == expected_valid


def test_split_valid_and_invalid_link_paths_unix_like():
    if os.name == 'nt':
        return

    all_attachments = {
        '/hello/dog\0/cat',
        'file:///K:/SPSS%20info/',
        'c:/SPSS%20inf',
        r'attachments\example_file.pdf',
    }

    expected_invalid = {
        '/hello/dog\0/cat',
    }

    expected_valid = {
        'file:///K:/SPSS%20info/',
        'c:/SPSS%20inf',
        r'attachments\example_file.pdf',
    }

    result = content_link_management.split_valid_and_invalid_link_paths(all_attachments)

    assert result.invalid == expected_invalid

    assert result.valid == expected_valid
