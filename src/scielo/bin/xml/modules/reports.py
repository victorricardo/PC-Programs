
import os
from datetime import datetime

import utils
import xml_utils
import content_validation

from article import Article, PersonAuthor, CorpAuthor, format_author


def report_date():
    procdate = datetime.now().isoformat()
    return procdate[0:10] + ' ' + procdate[11:19]


class TOCReport(object):

    def __init__(self, filename_and_article_list):
        self.articles = filename_and_article_list
        self.html_page = HTMLPage()

    def report(self):
        invalid = []
        equal_data = ['journal-title', 'journal id NLM', 'journal ISSN', 'publisher name', 'issue label', 'issue pub date', ]
        unique_data = ['order', 'doi', 'fpage', 'fpage seq', 'elocation id']

        toc_data = {}
        for label in equal_data + unique_data:
            toc_data[label] = {}

        for filename, article in self.articles:
            if article is None:
                invalid.append(filename)
            else:
                art_data = article.summary()
                for label in toc_data.keys():
                    toc_data[label] = utils.add_new_value_to_index(toc_data[label], art_data[label], filename)

        r = ''
        if len(invalid) > 0:
            r += self.html_page.format_div(self.html_page.format_message('ERROR: Invalid XML files'))
            r += self.html_page.format_div(self.html_page.format_list('', 'ol', invalid))

        for label in equal_data:
            if len(toc_data[label]) != 1:
                part = self.html_page.format_message('ERROR: equal value of ' + label + ' is required for all the articles of the package')
                for k, v in toc_data[label].items():
                    part += self.html_page.format_list('found ' + label + ' "' + k + '" in:', 'ul', v, 'issue-problem')
                r += part

        for label in unique_data:
            if len(toc_data[label]) > 0 and len(toc_data[label]) != len(self.articles):
                part = self.html_page.format_message('ERROR: unique value of ' + label + ' is required for all the articles of the package')
                for k, v in toc_data[label].items():
                    if len(v) > 1:
                        part += self.html_page.format_list('found ' + label + ' "' + k + ' in:', 'ul', v, 'issue-problem')
                r += part
        return self.html_page.format_div(r, 'issue-messages')


class ArticleDisplay(object):

    def __init__(self, article, html_page):
        self.article = article
        self.html_page = html_page

    def article_summary(self):
        r = ''
        r += self.toc_section
        r += self.article_type
        r += self.display_titles()
        r += self.doi
        r += self.article_id_other
        r += self.order
        r += self.fpage
        r += self.fpage_seq
        r += self.elocation_id
        r += self.article_date
        r += self.contrib_names
        r += self.contrib_collabs
        r += self.abstracts
        r += self.keywords
        r += self.sections
        r += self.formulas
        r += self.footnotes

        return self.html_page.format_div(r, 'article-data')

    def display_p(self, label, value, style=''):
        if value is None:
            value = 'None'
        return self.html_page.tag('p', self.html_page.tag('span', '[' + label + '] ', 'discret') + value, style)

    def display_titles(self):
        r = ''
        for t in self.article.title:
            r += self.html_page.tag('p', self.html_page.tag('span', '[' + t.language + ']', 'discret') + t.title, 'article-title')
        for t in self.article.trans_titles:
            r += self.html_page.tag('p', self.html_page.tag('span', '[' + t.language + ']', 'discret') + t.title, 'trans-title')
        return r

    def display_text(self, label, items):
        r = self.html_page.tag('p', label, 'label')
        for item in items:
            r += self.display_p(item.language, item.text)
        return self.html_page.tag('div', r)

    @property
    def toc_section(self):
        return self.display_p('toc section', self.article.toc_section, 'toc-section')

    @property
    def article_type(self):
        return self.display_p('@article-type', self.article.article_type, 'article-type')

    @property
    def article_date(self):
        return self.display_p('@article-date', self.article.article_pub_date)

    @property
    def contrib_names(self):
        return self.html_page.format_list('authors:', 'ol', [format_author(a) for a in self.article.contrib_names])

    @property
    def contrib_collabs(self):
        r = [format_author(a) for a in self.article.contrib_collabs]
        if len(r) > 0:
            r = self.html_page.format_list('collabs:', 'ul', r)
        else:
            r = self.display_p('collabs:', 'None')
        return r

    @property
    def abstracts(self):
        return self.display_text('abstracts', self.article.abstracts)

    @property
    def keywords(self):
        return self.html_page.format_list('keywords:', 'ol', ['(' + k['l'] + ') ' + k['k'] for k in self.article.keywords])

    @property
    def order(self):
        return self.display_p('order', self.article.order, 'order')

    @property
    def doi(self):
        return self.display_p('doi', self.article.doi, 'doi')

    @property
    def fpage(self):
        return self.display_p('pages', self.article.fpage + '-' + self.article.lpage, 'fpage')

    @property
    def fpage_seq(self):
        return self.display_p('fpage/@seq', self.article.fpage_seq, 'fpage')

    @property
    def elocation_id(self):
        return self.display_p('elocation-id', self.article.elocation_id, 'fpage')

    @property
    def article_id_other(self):
        return self.display_p('.//article-id[@pub-id-type="other"]', self.article.article_id_other, 'fpage')

    @property
    def sections(self):
        _sections = ['[' + sec_id + '] ' + sec_title + ' (' + str(sec_type) + ')' for sec_id, sec_type, sec_title in self.article.article_sections]
        return self.html_page.format_list('sections:', 'ul', _sections)

    @property
    def formulas(self):
        r = ''
        for item in self.article.formulas:
            r += self.html_page.tag('p', item)
        return r

    @property
    def footnotes(self):
        r = ''
        for item in self.article.article_fn_list:
            scope, fn_id, fn_type, fn_xml = item
            r += self.html_page.tag('p', scope + '[@id="' + fn_id + '" fn-type="' + fn_type + '"] ', 'label')
            r += self.html_page.tag('p', self.html_page.format_xml(fn_xml))
        return r

    def issue_header(self):
        r = [self.article.journal_title, self.article.journal_id_nlm_ta, self.article.issue_label, utils.format_date(self.article.issue_pub_date)]
        return self.html_page.tag('div', '\n'.join([self.html_page.tag('h5', item) for item in r if item is not None]), 'issue-data')


class ArticleReport(object):

    def __init__(self, article_validation, html_page):
        self.article_validation = article_validation
        self.html_page = html_page

    def display_items(self, items):
        r = ''
        for item in items:
            r += self.display_item(item)
        return r

    def display_item(self, item):
        return self.html_page.format_message(item)

    def sheet(self, content):
        r = ''
        r += '<table>'
        r += '<tr>'
        for label in ['label', 'status', 'message/value']:
            r += '<th>' + label + '</th>'
        r += '</tr>'
        r += content
        r += '</table>'
        return r

    def sheet_rows(self, table_data):
        r = ''

        for row in table_data:
            cell = ''
            cell += self.html_page.tag('td', row[0], 'label')
            cell += self.html_page.tag('td', row[1], '')

            style = self.html_page.message_style(row[1] + ':')
            value = row[2]
            if style == 'ok':
                value = self.html_page.tag('span', row[2], 'value')
            cell += self.html_page.tag('td', value)

            r += self.html_page.tag('tr', cell, style)
        return r

    def report(self):
        r = ''
        rows = self.html_page.tag('h2', 'article data')
        items = [self.article_validation.journal_title,
                    self.article_validation.publisher_name,
                    self.article_validation.journal_id,
                    self.article_validation.journal_id_nlm_ta,
                    self.article_validation.journal_issns,
                    self.article_validation.issue_label,
                    self.article_validation.article_type,
                    self.article_validation.toc_section,
                    self.article_validation.order,
                    self.article_validation.doi,
                    self.article_validation.fpage,
                    self.article_validation.language,
                    self.article_validation.total_of_pages,
                    self.article_validation.total_of_equations,
                    self.article_validation.total_of_tables,
                    self.article_validation.total_of_figures,
                    self.article_validation.total_of_references,
                    ]

        rows += self.sheet_rows(items)
        rows += self.sheet_rows(self.article_validation.titles)
        rows += self.sheet_rows(self.article_validation.trans_titles)
        rows += self.sheet_rows(self.article_validation.contrib_names)
        rows += self.sheet_rows(self.article_validation.contrib_collabs)
        rows += self.sheet_rows(self.affiliations)
        rows += self.sheet_rows(self.article_validation.funding)

        items = [
                    self.article_validation.license,
                    ]
        rows += self.sheet_rows(items)

        rows += self.sheet_rows(self.article_validation.history)
        rows += self.sheet_rows(self.article_validation.abstracts)
        rows += self.sheet_rows(self.article_validation.keywords)

        rows = self.sheet(rows)
        rows += self.references

        return self.html_page.format_div(rows, 'article-messages')

    def ref_person_groups(self, person_groups):
        r = ''
        for p in person_groups:
            if isinstance(p, PersonAuthor):
                r += self._contrib_name(p)
            elif isinstance(p, CorpAuthor):
                r += self.display_item(p.collab)
            else:
                print(type(p))
        return r

    @property
    def affiliations(self):
        r = []
        for a in self.article_validation.affiliations:
            label, status, xml = a
            if label == 'xml':
                r.append((label, status, self.html_page.format_xml(xml)))
            else:
                r.append(a)
        return r

    @property
    def references(self):
        rows = ''
        for ref in self.article_validation.references:
            rows += self.html_page.tag('h3', 'Reference ' + ref.id)
            r = []
            for item in ref.evaluate():
                r.append(item)
            rows += self.sheet(self.sheet_rows(r))
        return rows


class HTMLPage(object):

    def __init__(self):
        self.title = ''
        self.body = ''

    def html(self):
        s = ''
        s += '<html>'
        s += '<head>'
        s += '<meta charset="utf-8"/><title>' + self.title + '</title>'
        s += self.styles()
        s += '</head>'
        s += '<body>'
        s += self.tag('h1', self.title)
        s += self.tag('h3', report_date())
        s += self.body
        s += '</body>'
        s += '</html>'

        return s

    def styles(self):
        return '<style>' + open('./report.css', 'r').read() + '</style>'

    def body_section(self, style, anchor_name, title, content, sections=[]):
        anchor = anchor_name if anchor_name == '' else '<a name="' + anchor_name + '"/><a href="#top">^</a>'
        sections = '<ul class="sections">' + ''.join(['<li> [<a href="#' + s + '">' + t + '</a>] </li>' for s, t, d in sections]) + '</ul>'
        return anchor + '<' + style + '>' + title + '</' + style + '>' + sections + content

    def sheet(self, table_header_and_data, filename=None):
        table_header, table_data = table_header_and_data
        r = '<div>'
        r += '<table>'
        r += '<tr>'
        if filename is not None:
            r += '<th></th>'
        for label in table_header:
            r += '<th>' + label + '</th>'
        r += '</tr>'
        for row in table_data:
            r += '<tr>'
            if filename is not None:
                r += '<td>' + filename + '</td>'

            for label in table_header:
                r += '<td>' + self.format_cell(row.get(label), not label in ['filename', 'scope']) + '</td>'
            r += '</tr>'
        r += '</table>'
        r += '</div>'
        return r

    def format_div(self, content, style=''):
        return self.tag('div', content, style)

    def tag(self, tag_name, content, style=''):
        if tag_name == 'p' and '</p>' in content:
            tag_name = 'div'
        return '<' + tag_name + self.css_class(style) + '>' + content + '</' + tag_name + '>'

    def format_xml(self, value):
        value = value.replace('<', '&lt;')
        value = value.replace('>', '&gt;')
        return '<pre>' + value + '</pre>'

    def format_message(self, value):
        if '<p' in value:
            tag = 'div'
        else:
            tag = 'p'
        return '<' + tag + self.message_css_class(value) + '>' + value + '</' + tag + '>'

    def css_class(self, style):
        return ' class="' + style + '"' if style != '' else style

    def message_style(self, value):
        r = 'ok'
        if 'ERROR' in value:
            r = 'error'
        if 'WARNING' in value:
            r = 'warning'
        return r

    def message_css_class(self, style):
        return ' class="' + self.message_style(style) + '"'

    def format_list(self, label, list_type, list_items, style=''):
        r = ''
        r += '<div' + self.css_class(style) + '>'
        r += self.tag('p', (self.tag('span', label)))
        r += '<' + list_type + '>'
        if isinstance(list_items, dict):
            r += ''.join(['<li>' + self.display_label_value(k, v) + '</li>' for k, v in list_items.items()])
        elif isinstance(list_items, list):
            for item in list_items:
                if isinstance(item, dict):
                    for k, v in item.items():
                        r += '<li>' + self.display_label_value(k, v) + '</li>'
                else:
                    r += '<li>' + item + '</li>'
        r += '</' + list_type + '>'
        r += '</div>'
        return r

    def format_cell(self, value, is_data=True):
        r = '-'
        if value is None:
            r = '-'
        elif isinstance(value, str):
            r = value
        elif isinstance(value, dict):
            r += '<ul>'
            for k, v in value.items():
                if isinstance(v, list):
                    r += '<li>' + k + ': ' + ', '.join(v) + ';</li>'
                else:
                    r += '<li>' + self.display_label_value(k, v) + ';</li>'
            r += '</ul>'
        if is_data:
            r = '<span' + self.message_css_class(r) + '>' + r + '</span>'
        return r

    def save(self, filename, title=None, body=None):
        if title is not None:
            self.title = title
        if body is not None:
            self.body = body

        f = open(filename, 'w')
        r = self.html()
        if isinstance(r, unicode):
            r = r.encode('utf-8')
        f.write(r)
        f.close()

    def display_label_value(self, label, value):
        r = value if value is not None else 'None'
        return self.tag('span', label) + ' ' + r

    def format_p_label_value(self, label, value):
        return self.tag('p', self.display_label_value(label, value))

    def display_attributes(self, label, attributes):
        r = []
        for key, value in attributes.items():
            if value is list:
                value = '; '.join(value)
            r.append(display_label_value(key, value))
        return label + '\n' + '\n'.join(r) + '\n'

    def display_items_with_attributes(self, label, items_with_attributes):
        r = label + ': ' + '\n'
        for item_name, item_values in items_with_attributes.items():
            r += display_label_values_with_attributes(item_name, item_values)
        return r + '\n'

    def display_label_values_with_attributes(self, label, values_with_attributes):
        return label + ': ' + '\n' + '\n'.join([display_attributes('=>', item) for item in values_with_attributes]) + '\n'

    def conditional_required(self, label, value):
        return display_label_value(label, value) if value is not None else 'WARNING: Required ' + label + ', if exists. '

    def required(self, label, value):
        return display_label_value(label, value) if value is not None else 'ERROR: Required ' + label + '. '

    def required_one(self, label, value):
        return display_attributes(label, value) if value is not None else 'ERROR: Required ' + label + '. '

    def expected_values(self, label, value, expected):
        return display_label_value(label, value) if value in expected else 'ERROR: ' + value + ' - Invalid value for ' + label + '. Expected values ' + ', '.join(expected)

    def add_new_value_to_index(self, dict_key_and_values, key, value):
        print(key)
        if key is not None:
            if not key in dict_key_and_values.keys():
                dict_key_and_values[key] = []
            dict_key_and_values[key].append(value)
        return dict_key_and_values


class ArticleSheetData(object):

    def __init__(self, article, article_validation):
        self.article = article
        self.article_validation = article_validation

    def authors(self, filename=None):
        r = []
        t_header = ['xref', 'given-names', 'surname', 'suffix', 'prefix', 'collab', ]
        if not filename is None:
            t_header = ['filename', 'scope'] + t_header
        for a in self.article_validation.contrib_names:
            row = {}
            row['scope'] = 'article meta'
            row['filename'] = filename
            row['xref'] = ' '.join(a.xref)
            row['given-names'] = a.fname
            row['surname'] = a.surname
            row['suffix'] = a.suffix
            row['prefix'] = a.prefix
            r.append(row)

        for a in self.article_validation.contrib_collabs:
            row = {}
            row['scope'] = 'article meta'
            row['filename'] = filename
            row['collab'] = a.collab
            r.append(row)

        for ref in self.article_validation.references:
            for grp in ref.person_groups:
                for item in grp:
                    row = {}
                    row['scope'] = ref.id
                    row['filename'] = filename
                    if isinstance(item, PersonAuthor):
                        row['given-names'] = item.fname
                        row['surname'] = item.surname
                        row['suffix'] = item.suffix
                        row['prefix'] = item.prefix
                    elif isinstance(item, CorpAuthor):
                        row['collab'] = item.collab
                    else:
                        print(type(item))
                    r.append(row)
        return (t_header, r)

    def sources(self, filename=None):
        r = []
        t_header = ['ID', 'type', 'year', 'source', 'publisher name', 'location', ]
        if not filename is None:
            t_header = ['filename', 'scope'] + t_header

        for ref in self.article_validation.references:
            row = {}
            row['scope'] = ref.id
            row['ID'] = ref.id
            row['filename'] = filename
            row['type'] = ref.publication_type
            row['year'] = ref.year
            row['source'] = ref.source
            row['publisher name'] = ref.publisher_name
            row['location'] = ref.publisher_loc
            r.append(row)
        return (t_header, r)

    def ids(self):
        def _ids(node, scope):
            def _xref(xref_list):
                return '; '.join(['(' + xref_type + ') ' + xref_text for xref_rid, xref_type, xref_text in xref_list])

            res = []
            if node is not None:
                for n in node.findall('.//*[@id]'):
                    r = {}
                    r['scope'] = scope
                    r['element'] = n.tag
                    r['ID'] = n.attrib.get('id')
                    r['xref list'] = _xref(self.article.xref_list.get(n.attrib.get('id'), []))
                    res.append(r)
            return res

        r = []
        t_header = ['scope', 'ID', 'element', 'xref list']
        r += _ids(self.article.article_meta, 'article')
        r += _ids(self.article.body, 'article')
        r += _ids(self.article.back, 'article')

        for item in self.article.subarticles:
            r += _ids(item, 'sub-article ' + item.find('.').attrib.get('id', ''))
        for item in self.article.responses:
            r += _ids(item, 'response ' + item.find('.').attrib.get('id', ''))

        return (t_header, r)

    def tables(self):
        t_header = ['ID', 'label', 'caption', 'table', ]
        r = []
        for t in self.article.tree.findall('.//*[table]'):
            row = {}
            row['ID'] = t.attrib.get('id')
            row['label'] = t.findtext('.//label')
            row['caption'] = t.findtext('.//caption')

            table = xml_utils.node_text(t.find('./table'))
            if table is None:
                table = ''

            graphic = xml_utils.node_text(t.find('./graphic'))
            if graphic is None:
                graphic = ''
            row['table'] = table + graphic
            r.append(row)
        return (t_header, r)

    def hrefs(self, path=''):
        t_header = ['ID', 'Parent', 'Element', 'href', 'label', 'caption', ]
        r = []
        for parent in self.article.tree.findall('.//*[@{http://www.w3.org/1999/xlink}href]/..'):
            for elem in parent.findall('.//*[@{http://www.w3.org/1999/xlink}href]'):
                href = elem.attrib.get('{http://www.w3.org/1999/xlink}href')
                if ':' in href:
                    row = {}
                    row['Parent'] = parent.tag
                    row['Parent ID'] = parent.attrib.get('id', '')
                    row['label'] = parent.findtext('label')
                    row['caption'] = parent.findtext('caption')
                    row['Element'] = elem.tag
                    if elem.tag == 'graphic':
                        row['href'] = '<img src="' + path + href + '"/>'
                    else:
                        row['href'] = href
                    r.append(row)
        return (t_header, r)

    def affiliations(self):
        t_header = ['ID', 'data']
        r = []
        for a in self.article_validation.affiliations:
            row = {}
            row['ID'] = a.id
            data = {}
            data['ordered'] = ['original', 'orgname', 'norgname', 'orgdiv1', 'orgdiv2', 'orgdiv3', 'orgdiv2', 'city', 'state', 'country', 'xml']
            data['original'] = a.original
            data['norgname'] = a.norgname
            data['orgname'] = a.orgname
            data['orgdiv1'] = a.orgdiv1
            data['orgdiv2'] = a.orgdiv2
            data['orgdiv3'] = a.orgdiv3
            data['city'] = a.city
            data['state'] = a.state
            data['country'] = a.country
            data['xml'] = a.xml
            row['data'] = data
            r.append(row)
        return (t_header, r)


def statistics(content, word):
    return len(content.split(word)) - 1


def statistics_messages(e, f, w):
    s = [('Total of errors:', e), ('Total of fatal errors:', f), ('Total of fatal warnings:', w)]
    s = ''.join([HTMLPage().format_p_label_value(l, str(v)) for l, v in s])
    return HTMLPage().format_div(s, 'statistics')


def generate_package_reports(xml_path, report_path, report_filenames):
    report = HTMLPage()

    articles_and_filenames = []
    for xml_name in os.listdir(xml_path):
        if not 'incorrect' in xml_name and xml_name.endswith('.xml'):
            tree = xml_utils.load_xml(xml_path + '/' + xml_name)
            article = Article(tree)
            articles_and_filenames.append((xml_name, article))

    toc_validation = TOCReport(articles_and_filenames).report()
    toc_report_content = toc_validation

    authors_sheet_data = ''
    sources_sheet_data = ''

    if not os.path.isdir(report_path):
        os.makedirs(report_path)

    toc_e = 0
    toc_f = 0
    toc_w = 0
    for xml_name, article in articles_and_filenames:

        report_name = report_filenames[xml_name] + '.contents.html'
        article_validation = content_validation.ArticleContentValidation(article)
        data = ArticleSheetData(article, article_validation)
        display_data = ArticleDisplay(article, report)
        article_report = ArticleReport(article_validation, report)

        #authors_data = report.sheet(data.authors(xml_name))
        #sources_data = report.sheet(data.sources(xml_name))

        #authors_sheet_data += authors_data
        #sources_sheet_data += sources_data

        content = ''

        article_summary = ''
        article_summary += display_data.issue_header()
        article_summary += display_data.article_summary()

        # adiciona o sumario do artigo no toc report
        toc_report_content += report.tag('h2', xml_name) + article_summary

        content += article_summary
        content += article_report.report()

        toc_sections = []
        #toc_sections.append(('sec_affs', 'Affiliations', report.sheet(data.affiliations())))
        #toc_sections.append(('sec_hrefs', 'href', report.sheet(data.hrefs())))
        #toc_sections.append(('sec_tables', 'Tables', report.sheet(data.tables())))
        #toc_sections.append(('sec_ids', 'IDs', report.sheet(data.ids())))
        #toc_sections.append(('sec_authors', 'Authors', authors_data))
        #toc_sections.append(('sec_sources', 'Sources', sources_data))

        for toc_sec in toc_sections:
            anchor, sec_title, sec_data = toc_sec
            content += report.body_section('h2', anchor, sec_title, sec_data)

        e = statistics(content, 'ERROR:')
        f = statistics(content, 'FATAL ERROR:')
        e = e - f
        w = statistics(content, 'WARNING:')

        toc_e += e
        toc_f += f
        toc_w += w
        report.title = xml_name + ' - Contents validation report'
        report.body = statistics_messages(e, f, w) + content
        report.save(report_path + '/' + report_name)

    report.title = 'Authors'
    report.body = authors_sheet_data
    report.save(report_path + '/authors.html')

    report.title = 'Sources'
    report.body = sources_sheet_data
    report.save(report_path + '/sources.html')

    report.save(report_path + '/toc.html', 'TOC Report', statistics_messages(toc_e, toc_f, toc_w) + toc_report_content)

xml_path = '/Users/robertatakenaka/Documents/vm_dados/scielo_data/serial/pab/v48n7/markup_xml/scielo_package'
report_path = '/Users/robertatakenaka/Documents/vm_dados/scielo_data/_xpm_reports_'
report_filenames = {v:v.replace('.xml', '') for v in os.listdir(xml_path) if v.endswith('.xml') and not 'incorre' in v }
generate_package_reports(xml_path, report_path, report_filenames)
print('Reports in ' + report_path)
