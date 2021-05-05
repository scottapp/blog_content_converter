from nbconvert import MarkdownExporter
from nbconvert.writers import FilesWriter
from nbconvert.nbconvertapp import NbConvertApp


def convert_notebook(src_path):
    app = NbConvertApp()
    app.output_files_dir = './stage/img'
    app.writer = FilesWriter()
    app.exporter = MarkdownExporter()
    app.convert_single_notebook(src_path)


def main():
    #src_path = '4-cifar10_tutorial.ipynb'
    src_path = '203_activation.ipynb'
    convert_notebook(src_path)


if __name__ == '__main__':
    main()

print('done')
