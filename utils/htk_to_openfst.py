#!/usr/bin/env python
# coding: utf-8
import re
import argparse
import sys
import gzip

NULL_SYMBOL = "!NULL"
EPS_SYMBOL = "<eps>"


def parse_htk_header(htk_file_txt):
    htk_header = dict()
    size_pattern = re.compile(r"^(?:NODES|N)=([-+]?\d+)\s+" +
                              r"(?:LINKS|L)=([-+]?\d+)")
    offset = 0
    for line in htk_file_txt:
        offset += 1
        m = re.match(size_pattern, line)
        if m:
            htk_header["Nodes"] = int(m.group(1))
            htk_header["Links"] = int(m.group(2))
            htk_header["Header Size"] = offset
            return htk_header

    raise RuntimeError("No header found in htk file!")


def parse_node_line(line):
    # node line syntax:  'I=%d\tt=%f\n'
    node_pattern = re.compile(
        r'I=([-+]?\d+)\s+t=(([-+]?\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)')
    m = re.match(node_pattern, line)
    if m:
        return {'I': int(m.group(1)), 't': float(m.group(2))}
    else:
        raise RuntimeError("Malformed Node line!")


def parse_nodes(node_lines):
    return [parse_node_line(line) for line in node_lines]


def parse_link_line(line):
    # link line syntax:  'J=%d\tS=%d\tE=%d\tW=%s\tv=%f\ta=%f\tl=%f\n'
    import re    
    node_pattern = re.compile(
        r'J=([-+]?\d+)\s+S=([-+]?\d+)\s+' +
        r'E=([-+]?\d+)\s' +
        r'+W=([\w!]+)\s+' +
        r'v=([-+]?\d+(?:\.\d*)?|\.\d+[eE][-+]?\d+)\s+' +
        r'a=([-+]?\d+(?:\.\d*)?|\.\d+[eE][-+]?\d+)\s+' +
        r'l=([-+]?\d+(?:\.\d*)?|\.\d+[eE][-+]?\d+)'
    )
    m = re.match(node_pattern, line)
    if m:
        return {'J': int(m.group(1)),
                'S': int(m.group(2)),
                'E': int(m.group(3)),
                'W': m.group(4).replace(NULL_SYMBOL, EPS_SYMBOL),
                'v': float(m.group(5)),
                'AM': float(m.group(6)),
                'LM': float(m.group(7))
                }
    else:
        raise RuntimeError("Malformed Link line!")


def parse_links(link_lines):
    return [parse_link_line(line) for line in link_lines]


def determine_final_nodes(links, num_nodes):
    link_start_states = {link['S'] for link in links}
    nodes = {i for i in range(num_nodes)}
    return nodes - link_start_states


def parse_htk_lattice(htk_txt_lines):
    htk_header = parse_htk_header(htk_txt_lines)
    offset_nodes = htk_header["Header Size"]
    offset_links = offset_nodes + htk_header['Nodes']
    nodes = parse_nodes(htk_txt_lines[offset_nodes:offset_links])
    links = parse_links(htk_txt_lines[offset_links:])
    final_nodes = determine_final_nodes(links, htk_header['Nodes'])
    return {'header': htk_header,
            'nodes': nodes, 
            'links': links,
            'final_nodes': final_nodes}


def get_openfst_content(htk_lattice):
    ofst_content = [
        '{S}\t{E}\t{IN}\t{OUT}\t{WEIGHT}\n'.format(
                S=link['S'],
                E=link['E'],
                IN=link['W'],
                OUT=link['W'],
                WEIGHT=link['AM']
        ) for link in htk_lattice['links']
    ]

    ofst_content.extend(['{}\n'.format(final_id) 
                         for final_id in htk_lattice['final_nodes']])
    return ofst_content


def convert_htk_to_openfst(htk_filename, ofst_file, syms_filename=None):

    if htk_filename == '-':
        htk_file = sys.stdin
    else:
        htk_file = open(htk_filename, 'r')

    htk_content = [line for line in htk_file.readlines()
                       if line.strip() != '']
    htk_file.close()

    htk_lattice = parse_htk_lattice(htk_content)

    for line in get_openfst_content(htk_lattice):
        ofst_file.write(line)

    if syms_filename:
        sym_table = parse_symbols_from_htk(htk_lattice)
        with open(syms_filename, 'w') as syms_file:
            for line in sym_table:
                syms_file.write(line)


def create_symtable(wordsyms):
    sym_table = [EPS_SYMBOL + '\t0\n', '<space>\t1\n']
    sym_table.extend(['{}\t{}\n'.format(wlabel, wid)
                      for wid, wlabel in enumerate(wordsyms, start=2)])
    return sym_table


def parse_symbols_from_htk(htk_lattice):
    return create_symtable(set([link['W'] for link in htk_lattice['links']]))


def parse_symbols_from_openfst(openfst_content):
    return create_symtable(set([line.split('\t')[2]
                                for line in openfst_content
                                if len(line.split('\t')) > 2]))


def main():
    """expected format:
              r'VERSION=%d.%d.%d\n' +
              r'UTTERANCE=%s\n' +
              r'N=%d\tL=%d\n' +
              r'N Nodelines: I=%d\tt=%f\n' +
              r'L Linklines: J=%d\tS=%d\tE=%d\tW=%s\tv=%f\ta=%f\tl=%f\n'
    """
    
    parser = argparse.ArgumentParser(
        description="Convert an htk SLF file to openfst text format."
                    "This function can produce an optional symbols file if"
                    " needed. In this case, the symbols file is only valid for"
                    " the single lattice it was extracted from.")

    parser.add_argument(
        'htk_filename', metavar='HTK_FILE', nargs='?',
        type=str, default='-',
        help=("The input file in htk SLF format with syntax as descibed.\n"
              "default: - "
              "In that case, stdin is used as input file.")
    )
    
    parser.add_argument(
        'ofst_file', metavar='OPENFST_FILE', type=argparse.FileType('w'),
        default=sys.stdout, nargs='?',
        help=("The output file to be produced in openfst text format. "
              "default: stdout")
    )

    parser.add_argument(
        '--syms_filename', metavar='SYMS_FILE', type=str,
        default='syms.txt', nargs='?',
        help='The optional openfst symbol file to be produced'
    )
    args = parser.parse_args()
    
    convert_htk_to_openfst(args.htk_filename,
                           args.ofst_file,
                           args.syms_filename)


if __name__ == "__main__":
    main()
