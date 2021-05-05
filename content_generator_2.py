import os
import shutil
import tempfile
import git
import collections
from nbconvert import MarkdownExporter
from nbconvert.writers import FilesWriter
from nbconvert.nbconvertapp import NbConvertApp


def convert_notebook(src_path, output_img_dir):
    app = NbConvertApp()
    app.output_files_dir = output_img_dir
    app.writer = FilesWriter()
    app.exporter = MarkdownExporter()
    app.convert_single_notebook(src_path)


def clone(top_repo_dir, repo_url):
    git.Git(top_repo_dir).clone(repo_url)


def get_project_readme(top_repo_dir, project_name):
    readme_path = '%s/%s/README.md' % (top_repo_dir, project_name)
    if not os.path.isfile(readme_path):
        assert False, 'error readme file' % project_name

    with open(readme_path, 'r', encoding='utf8') as f:
        lines = f.readlines()
        return lines


def replace_title(lines, repo_url, new_title):
    first_line = lines[0]
    if first_line.startswith('# '):
        if repo_url:
            front_matter = ['---\n', 'title: %s\n' % new_title, '---\n', 'my github: %s\n' % repo_url]
        else:
            front_matter = ['---\n', 'title: %s\n' % new_title, '---\n']
        return front_matter + lines[1:]
    return lines


def replace_title_2(lines):
    first_line = lines[0]
    if first_line.startswith('# '):
        new_title = first_line[2:].strip()
        front_matter = ['---\n', 'title: %s\n' % new_title, '---\n']
        return front_matter + lines[1:]
    return lines


class Topic(object):
    def __init__(self, topic):
        self.topic = topic
        self.categories = collections.OrderedDict()

    def add_doc(self, category, doc):
        if category in self.categories.keys():
            docs = self.categories[category]
        else:
            docs = []

        docs.append(doc)
        self.categories[category] = docs

    def get_categories(self):
        return self.categories


def main(tmp_repo_dir):
    output_dir = './output'

    with open('blog_content.csv', 'r', encoding='utf8') as f:
        lines = f.readlines()

    topics = collections.OrderedDict()

    index_page_content = []

    for line in lines:
        try:
            if not line.strip():
                continue

            print(line.strip())
            cols = line.split(',')
            assert len(cols) >= 2, 'error data, %s' % line

            repo_url = cols[0].strip()
            new_title = cols[3].strip()
            topic_name = cols[1].strip()
            category = cols[2].strip()
            topic_dir_lower = str.lower(cols[1].strip().replace(' ', '_'))
            project_name = repo_url.split('/')[-1]

            if not os.path.isdir('%s/%s' % (output_dir, topic_dir_lower)):
                os.makedirs('%s/%s' % (output_dir, topic_dir_lower), mode=0o755)

            clone(tmp_repo_dir, repo_url)
            lines = get_project_readme(tmp_repo_dir, project_name)
            new_lines = replace_title(lines, repo_url, new_title)

            # save modified readme.md file
            with open('%s/%s/%s.md' % (output_dir, topic_dir_lower, project_name), 'w') as f:
                f.writelines(new_lines)

            if topic_name in topics.keys():
                topic = topics[topic_name]
            else:
                topic = Topic(topic_name)
                topics[topic_name] = topic

            md_files = list()
            if os.path.isdir('%s/%s/workspace/' % (tmp_repo_dir, project_name)):
                files = os.listdir('%s/%s/workspace/' % (tmp_repo_dir, project_name))
                for file in files:
                    if not file.endswith('.ipynb'):
                        continue
                    src_path = '%s/%s/workspace/%s' % (tmp_repo_dir, project_name, file)
                    output_img_dir = '/img/%s/%s' % (project_name, file.split('.')[0])
                    convert_notebook(src_path, output_img_dir)

                files = os.listdir('%s/%s/workspace/' % (tmp_repo_dir, project_name))
                for file in files:
                    if file.endswith('.md'):
                        md_files.append(file)

            if md_files:
                if not os.path.isdir('%s/%s/%s' % (output_dir, topic_dir_lower, project_name)):
                    os.makedirs('%s/%s/%s' % (output_dir, topic_dir_lower, project_name), mode=0o755)

                #index_page_content.append('## %s\n' % new_title)
                #index_page_content.append('- [README](/docs/%s/%s)\n' % (topic_dir_lower, project_name))

                md_docs = collections.OrderedDict()
                tmp = list()

                """
                print("'%s sidebar': {" % new_title)
                print("\t'Back To Top': [")
                print("\t\t'%s/index'," % topic_dir_lower)
                print("\t],")
                print("\t'%s': [" % new_title)
                print("\t\t'%s/%s'," % (topic_dir_lower, project_name))
                """
                tmp.append("'%s/%s'," % (topic_dir_lower, project_name))
                for file in md_files:
                    src_path = '%s/%s/workspace/%s' % (tmp_repo_dir, project_name, file)
                    dst_path = '%s/%s/%s/%s' % (output_dir, topic_dir_lower, project_name, file)
                    with open(src_path, 'r', encoding='utf8') as f:
                        tmp_content = f.readlines()
                    new_content = replace_title_2(tmp_content)
                    with open(src_path, 'w', encoding='utf8') as f:
                        f.writelines(new_content)
                    shutil.copy2(src_path, dst_path)
                    tmp.append("'%s/%s/%s'," % (topic_dir_lower, project_name, file.split('.')[0]))
                    #print("\t\t'%s/%s/%s'," % (topic_dir_lower, project_name, file.split('.')[0]))
                    #url = "%s/%s/%s" % (topic_dir_lower, project_name, file.split('.')[0])
                    #index_page_content.append('- [%s](/docs/%s)\n' % (file.split('.')[0], url))

                md_docs[new_title] = tmp
                topic.add_doc(category, md_docs)

                """
                print("\t],")
                print("},")
                """
            else:
                topic.add_doc(category, '%s/%s' % (topic_dir_lower, project_name))

        except Exception as ex:
            print(ex)
            assert False

    for topic_name, topic in topics.items():
        categories = topic.get_categories()
        print("'%s': {" % topic_name)
        for category_name, docs in categories.items():
            print("\t'%s': [" % category_name)
            for doc in docs:
                if isinstance(doc, str):
                    print("\t\t'%s'," % doc)
                else:
                    project_name = list(doc.keys())[0]
                    md_docs = doc[project_name]
                    print("\t{")
                    print("\t\t'%s': [" % project_name)
                    for md_doc in md_docs:
                        print("\t\t\t%s" % md_doc)
                    print("\t\t]")
                    print("\t},")
            print("\t],")
        print("},")

    """
    with open('%s/index.md' % (output_dir), 'w', encoding='utf8') as f:
        f.writelines(index_page_content)
    """


def convert_files():
    project_name = 'test'

    project_name_lower = project_name.lower()
    source_dir = './source/%s' % project_name_lower
    stage_dir = './stage/%s' % project_name_lower

    if not os.path.isdir(stage_dir):
        os.makedirs(stage_dir)

    files = os.listdir(source_dir)
    for filename in files:
        if not filename.endswith('.ipynb'):
            continue

        src_path = '%s/%s' % (source_dir, filename)
        src_md_path = '%s/%s.md' % (source_dir, filename.split('.')[0])
        dst_md_path = '%s/%s.md' % (stage_dir, filename.split('.')[0])

        output_img_dir = '/img/%s/%s' % (project_name_lower, filename.split('.')[0])
        convert_notebook(src_path, output_img_dir)

        shutil.move(src_md_path, dst_md_path)


def convert_file(source_dir, topic, project_name, file_name, title):
    assert file_name.endswith('.ipynb'), 'error file format, %s' % file_name

    source_project_dir = '%s/%s/%s' % (source_dir, topic, project_name)
    stage_dir = './stage/%s/%s' % (topic, project_name)

    src_path = '%s/%s' % (source_project_dir, file_name)
    src_md_path = '%s/%s.md' % (source_project_dir, file_name.split('.')[0])
    dst_md_path = '%s/%s.md' % (stage_dir, file_name.split('.')[0])

    output_img_dir = '/img/%s/%s/%s' % (topic, project_name, file_name.split('.')[0])
    convert_notebook(src_path, output_img_dir)

    with open(src_md_path, 'r', encoding='utf8') as f:
        tmp_content = f.readlines()
    new_content = replace_title(tmp_content, '', title)
    with open(src_md_path, 'w', encoding='utf8') as f:
        f.writelines(new_content)

    shutil.move(src_md_path, dst_md_path)


def convert_project(source_dir, topic_name, project_name):
    with open('%s/%s/%s/pages_data.csv' % (source_dir, topic_name, project_name), 'r') as f:
        lines = f.readlines()

    if not os.path.isdir('./stage/%s/%s' % (topic_name, project_name)):
        os.makedirs('./stage/%s/%s' % (topic_name, project_name))

    for line in lines:
        if not line:
            continue

        data = line.strip().split(',')

        assert project_name == data[2].strip(), 'error project name, %s, %s' % (project_name, data[2])
        file_name = data[0].strip()
        topic = data[1].strip()
        sidebar_title = data[3].strip()
        print('processing - ', topic, project_name, file_name, sidebar_title)

        convert_file(source_dir, topic, project_name, file_name, sidebar_title)


if __name__ == '__main__':

    source_dir = './source'
    topic_name = 'SageMaker'

    projects = list()
    files = os.listdir('%s/%s' % (source_dir, topic_name))
    for file in files:
        if os.path.isdir('%s/%s/%s' % (source_dir, topic_name, file)):
            projects.append(file)

    for project in projects:
        convert_project(source_dir, topic_name, project)
