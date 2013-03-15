import sys
from PyQt4 import QtCore, QtGui, Qsci


class MapLexer(Qsci.QsciLexerCustom):
      def __init__(self, parent):
            Qsci.QsciLexerCustom.__init__(self, parent)
            self._styles = {
                 0: 'Default',
                 1: 'Comment',
                 2: 'Object',
                 3: 'Parameter',
                 4: 'Value',
                 5: 'Deprecated',
                 }
            for key,value in self._styles.iteritems():
                 setattr(self, value, key)

      def description(self, style):
            return self._styles.get(style, '')

      def defaultColor(self, style):
            if style == self.Default:
                 return QtGui.QColor('#000000')
            elif style == self.Comment:
                 return QtGui.QColor('#C0C0C0')
            elif style == self.Object:
                 return QtGui.QColor('#000099')
            elif style == self.Parameter:
                 return QtGui.QColor('#990099')
            elif style == self.Value:
                 return QtGui.QColor('#00CC00')
            elif style == self.Deprecated:
                 return QtGui.QColor('#CC0000')
            return Qsci.QsciLexerCustom.defaultColor(self, style)

      def styleText(self, start, end):
            editor = self.editor()
            if editor is None:
                 return

            # scintilla works with encoded bytes, not decoded characters.
            # this matters if the source contains non-ascii characters and
            # a multi-byte encoding is used (e.g. utf-8)
            source = ''
            if end > editor.length():
                 end = editor.length()
            if end > start:
                 if sys.hexversion >= 0x02060000:
                      # faster when styling big files, but needs python 2.6
                      source = bytearray(end - start)
                      editor.SendScintilla(
                            editor.SCI_GETTEXTRANGE, start, end, source)
                 else:
                      source = unicode(editor.text()).encode('utf-8')[start:end]
            if not source:
                 return

            # the line index will also be needed to implement folding
            index = editor.SendScintilla(editor.SCI_LINEFROMPOSITION, start)
            if index > 0:
                 # the previous state may be needed for multi-line styling
                 pos = editor.SendScintilla(
                              editor.SCI_GETLINEENDPOSITION, index - 1)
                 state = editor.SendScintilla(editor.SCI_GETSTYLEAT, pos)
            else:
                 state = self.Default

            set_style = self.setStyling
            self.startStyling(start, 0x1f)

            # scintilla always asks to style whole lines
            token = ''

            LEX_STATE_INIT    = 0
            LEX_STATE_COMMENT = 1
            LEX_STATE_IN_SINGLE_QUOTES = 2
            LEX_STATE_IN_DOUBLE_QUOTES = 3

            state = LEX_STATE_INIT

            for c in source:

                 token += chr(c)

                 if state == LEX_STATE_INIT and chr(c) == '#':
                    state = LEX_STATE_COMMENT
	            
                 elif state == LEX_STATE_INIT and chr(c) == '\'':
                    state = LEX_STATE_IN_SINGLE_QUOTES

                 elif state == LEX_STATE_INIT and chr(c) == '"':
                    state = LEX_STATE_IN_DOUBLE_QUOTES

                 elif state == LEX_STATE_IN_SINGLE_QUOTES and chr(c) == '\'':
                    state = LEX_STATE_INIT
                    print 'VALUE: %s' % token 
                    set_style(len(token), self.Value)
                    token = '' 

                 elif state == LEX_STATE_IN_DOUBLE_QUOTES and chr(c) == '"':
                    state = LEX_STATE_INIT
                    print 'VALUE: %s' % token 
                    set_style(len(token), self.Value)
                    token = '' 

                 elif state == LEX_STATE_COMMENT and chr(c) == '\n':
                    state = LEX_STATE_INIT
                    print 'COMMENT: %s' % token 
                    set_style(len(token), self.Comment)
                    token = '' 

                 elif state == LEX_STATE_INIT and chr(c).isspace() :
                    dict = ['CLASS', 'END', 'FEATURE', 'JOIN', 'LABEL', 'LAYER', 'LEADER', 'LEGEND', 'MAP', 'METADATA', 'OUTPUTFORMAT', 'PATTERN', 'POINTS', 'PROJECTION', 'QUERYMAP', 'REFERENCE', 'SCALEBAR', 'STYLE', 'SYMBOL', 'VALIDATION', 'WEB']
                    for i in dict:
                          pos = token.find(i) 
                          if pos >= 0:
                              set_style(len(token), self.Object)
                              print 'OBJECT: %s' % token 
                              token = '' 
			      break
		    dict = ['ALIGN', 'ALPHACOLOR', 'ANCHORPOINT', 'ANGLE', 'BACKGROUNDCOLOR', 'BUFFER', 'CENTER', 'CHARACTER', 'CLASSGROUP', 'CLASSITEM', 'OUTLINECOLOR', 'COLOR', 'COLORRANGE', 'CONFIG', 'CONNECTION', 'CONNECTIONTYPE', 'DATA', 'DATAPATTERN', 'DATARANGE', 'DEBUG', 'DEFRESOLUTION', 'DRIVER', 'EMPTY', 'ENCODING', 'ERROR', 'EXPRESSION', 'EXTENSION', 'EXTENT', 'FILLED', 'FILTER', 'FILTERITEM', 'FONT', 'FONTSET', 'FOOTER', 'FORCE', 'FORMATOPTION', 'FROM', 'GAP', 'GEOMTRANSFORM', 'GRATICULE', 'GRID', 'GRIDSTEP', 'GROUP', 'HEADER', 'IMAGECOLOR', 'IMAGEMODE', 'IMAGEPATH', 'IMAGEQUALITY', 'IMAGETYPE', 'IMAGEURL', 'IMAGE', 'INCLUDE', 'INDEX', 'INITIALGAP', 'INTERVALS', 'ITEMS', 'KEYIMAGE', 'KEYSIZE', 'KEYSPACING', 'LABELCACHE_MAP_EDGE_BUFFER', 'LABELCACHE', 'LABELFORMAT', 'LABELITEM', 'LABELMAXSCALEDENOM', 'LABELMINSCALEDENOM', 'LABELREQUIRES', 'LABELSIZEITEM', 'LATLON', 'LINECAP', 'LINEJOIN', 'LINEJOINMAXSIZE', 'LOG', 'MARKER', 'MARKERSIZE', 'MASK', 'MAXARCS', 'MAXBOXSIZE', 'MAXDISTANCE', 'MAXFEATURES', 'MAXINTERVAL', 'MAXLENGTH', 'MAXOVERLAPANGLE', 'MAXSCALE', 'MAXSCALEDENOM', 'MAXSIZE', 'MAXSUBDIVIDE', 'MAXTEMPLATE', 'MAXWIDTH', 'MIMETYPE', 'MINARCS', 'MINBOXSIZE', 'MINDISTANCE', 'MINFEATURESIZE', 'MININTERVAL', 'MINSCALE', 'MINSCALEDENOM', 'MINSIZE', 'MINSUBDIVIDE', 'MINTEMPLATE', 'MINWIDTH', 'NAME', 'OFFSET', 'OFFSITE', 'OPACITY', 'OUTLINEWIDTH', 'PARTIALS', 'POLAROFFSET', 'POSITION', 'POSTLABELCACHE', 'PRIORITY', 'PROCESSING', 'QUERYFORMAT', 'REPEATDISTANCE', 'REQUIRES', 'RESOLUTION', 'SCALE', 'SHADOWCOLOR', 'SHADOWSIZE', 'SHAPEPATH', 'SIZE', 'SIZEUNITS', 'STATUS', 'STYLEITEM', 'SYMBOLSCALE', 'SYMBOLSCALEDENOM', 'SYMBOLSET', 'TABLE', 'TEMPLATE', 'TEMPLATEPATTERN', 'TEXT', 'TILEINDEX', 'TILEITEM', 'TITLE', 'TO', 'TOLERANCE', 'TOLERANCEUNITS', 'TRANSFORM', 'TRANSPARENT', 'TYPE', 'UNITS', 'WIDTH', 'WRAP']
                    for i in dict:
                          pos = token.find(i) 
                          if pos >= 0:
                              set_style(len(token), self.Parameter)
                              print 'Parameter: %s' % token 
                              token = '' 
			      break
                    set_style(len(token), self.Default)
                    print 'DEFAULT: %s' % token 
                    token = '' 
