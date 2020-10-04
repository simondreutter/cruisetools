import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QVBoxLayout, QLabel, QToolBox, QPushButton, QTextEdit, QLineEdit)
from PyQt5.QtGui import QColor,QFont,QIcon


class ReadmeWindow(QWidget):

    def __init__(self,readme_text):
        '''Initialize ReadmeWindow'''
        super().__init__()
        # icon path
        self.icon_path = ':/plugins/cruisetools/icons'
        
        # set window size
        self.resize(600, 570)
        
        # set window icon
        icon = QIcon(f'{self.icon_path}/icon.png')
        self.setWindowIcon(icon)
        
        # set windows title
        self.setWindowTitle('Readme')
        
        # create layout
        layout = QGridLayout()
        
        # create title, big font, centered
        title = QLabel()
        title.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        title_font = QFont('Default', 14, QFont.Bold)
        title.setFont(title_font)
        
        # add title to layout
        layout.addWidget(title, 0, 0)
        
        # create version text, centered under title
        version = QLabel()
        version.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        version_font = QFont('Default', 10)
        version.setFont(version_font)
        
        # add version to layout
        layout.addWidget(version, 1, 0)
        
        # create toolbox
        toolbox = QToolBox()
        
        # toolbox styleSheet
        toolbox_style = '''
                            QToolBox::tab {
                                border: 1px solid #C4C4C3;
                                font-size: 9pt;
                            }
                            QToolBox::tab:selected {
                                background-color: RGB(200, 0, 200);
                            }
                        '''
        
        # set toolbox style
        toolbox.setStyleSheet(toolbox_style)
        
        # add toolbox to layout
        layout.addWidget(toolbox, 2, 0)
        
        # splot readme text in text blocks
        blocks = readme_text.split('\n## ')
        
        # handle title and version block
        for line in blocks[0].splitlines():
            line = line.strip()
            if line.startswith('# '):
                title_text = line.replace("# ","")
            elif line.startswith('*v'):
                version_text = line.replace("*","")
        
        # set version and title text
        title.setText(title_text)
        version.setText(version_text)
        
        # create toolbox content from text blocks
        idx = 0
        for block in blocks[1:]:
            # get block title and content
            block_title,md = block.split('\n',1)
            
            # convert markdown to html (cheap way) << setMarkdown in PyQt 5.15
            html = self.markdown(md)
            
            # create text field
            text = QTextEdit()
            
            # mak text field read only
            text.setReadOnly(True)
            
            # add content
            text.setHtml(html)
            
            # add text to toolbox
            toolbox.addItem(text, block_title)
            
            # get block icon
            icon = self.get_icon(block_title)
            
            # set block icon
            toolbox.setItemIcon(idx,icon)
            
            idx = idx + 1
        
        # set window layout
        self.setLayout(layout)

    def markdown(self,md):
        '''Convert Markdown Readme to HTML (cheap solution)

        Parameters
        ----------
        md : str
            markdown text

        Returns
        -------
        html : str
            converted markdown string in html

        '''
        # empty list for html lines
        html_list = []
        # loop over lines in block text
        for line in md.splitlines():
            line = line.strip()
            # if line is heading 3 make it bold
            if line.startswith('### '):
                if line.startswith('### Installation'):
                    break
                else:
                    line = f'<b>{line.replace("### ","")}</b><br>'
            #if line is a url make it a link
            if line.startswith('http'):
                line = f'<br><a href="{line}">{line}</a><br>'
            # clean up some markup stuff
            line = line.replace('\\*','*')
            line = line.replace('**','')
            line = line.replace('`','')
            line = line.replace('___','<hr>')
            
            # add line to html list
            html_list.append(line)
        
        # join html list with line breaks
        html = f'{"<br>".join(html_list)}<br>'
        
        return html

    def get_icon(self,title):
        '''Get Icon for Readme Dialog

        Parameters
        ----------
        title : str
            menu title

        Returns
        -------
        icon : QIcon
            icon to be displayed in the toolbox

        '''
        title = title.lower()
        if title == 'bathymetry':
            icon = QIcon(f'{self.icon_path}/bathymetry_menu.png')
        elif title == 'contour':
            icon = QIcon(f'{self.icon_path}/create_contours.png')
        elif title == 'vector':
            icon = QIcon(f'{self.icon_path}/vector_menu.png')
        elif title == 'planning':
            icon = QIcon(f'{self.icon_path}/planning_menu.png')
        else:
            icon = QIcon(f'{self.icon_path}/icon_grey.png')
        
        return icon
