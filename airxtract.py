import sys
import re
import json

def read_binary_range_in_file(filename, start="0", end="end_of_file"):
    """
    Reads a binary file from a given start and end offset and returns the data.
    If no start or end is defined, the entire file is read.
    If a start but no end is defined, the entire file after the start offset is read

    Args:
        filename (str): Path to the file to extract data from
        start (str): offset to start reading from
        end (str): offset to end file read at

    Returns:
        data (bytes): The data read from the file between the given offset parameters
    """
    try:
        with open(filename,'rb') as file:
            start = int(start, 16)
            file.seek(start)
            if end == "end_of_file":
                data = file.read()
            else:
                end = int(end, 16)
                data = file.read(end - start)
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

    file.close()
    return data

def find_offsets(data,pattern):
    """
    Finds offsets in a bytes object that match a given pattern
    Args:
        data (bytes): data to search offsets in
        pattern (bytes): The partterns that deliniate the start and end of a block

    Returns:
        offsets (array): list of offsets found in the data for the searched pattern
    """
    offsets = []
    s = 0
    while True:
        index = data.find(pattern, s)
        if index == -1:
            break
        offsets.append(hex(index))
        s = index + len(pattern)

    size = len(offsets)
    blocks = []
    for i in range(size):
        section = [0,0]
        if i+1 >= size:
            break
        section[0] = offsets[i]
        section[1] = offsets[i+1]
        blocks.append(section)
    return blocks

def extract_sections(filename):
    """
    Parses a binary rules to map each of it's sections into a dictionary structure.
    First pass looks for sections delimited by FF FF FF FF bytes throughout the file.
    A second pass looks for subsections between each of those sections delimited by 
    00 00 00.

    Args
    filename (str) : path to a logrhythm rules export file.

    Returns
    file_sections (dict) : dictionary with string descriptions of each section and subsection 
    found in the file <filename>

    {
        name: section_<iteration>
        offset_1: <0x start index> (in reference to the file)
        offset_2: <0x end index> (in reference to the file)
        section_start: <0x start index>
        section_end: <0x end index>
        size: <number of bytes>
        is_empty: <bool>

        subsections [
        {
            name: sub_section_<iteration>
            offset_1: <0x start index> (in reference to the file)
            offset_2: <0x end index> (in reference to the file)
            start: <0x start index> (in reference to the subsection)
            end: <0x end index> (in reference to the subsection)
            size: <number of bytes>
            is_empty: <bool>
        },
        ...
        ]
    },
    ...
    """
    data = read_binary_range_in_file(filename)
    section_pattern = b'\xFF\xFF\xFF\xFF'
    sections = find_offsets(data, section_pattern) 

    extracted_sections = []
    for i in range(len(sections)):
        section_start = int(sections[i][0],16)
        section_end = int(sections[i][1],16)
        section_size = section_end - section_start

        is_empty = section_size <= len(section_pattern)

        sub_section = read_binary_range_in_file(filename, sections[i][0], sections[i][1])
        sub_section_pattern = b'\x00\x00\x00'
        sub_section_ranges = find_offsets(sub_section,sub_section_pattern)

        section = {
            "name":"section_" + str(i),
            "section_start": sections[i][0],
            "section_end": sections[i][1],
            "size": section_size,
            "is_empty": is_empty,
        }

        sub_sections = [{}] * len(sub_section_ranges)
        for j in range(len(sub_section_ranges)):
            sub_section_start = int(sub_section_ranges[j][0],16)
            sub_section_end = int(sub_section_ranges[j][1],16)
            sub_section_size = sub_section_end - sub_section_start


            offset_1 = sub_section_end + section_end - len(sub_section_pattern)
            offset_2 = sub_section_end + section_end - len(sub_section_pattern)

            if j == 0:
                offset_1 = sub_section_start + section_end - len(section_pattern)


            is_empty = sub_section_size <= len(sub_section_pattern)


            cur_sub_sect = {
                "name":"sub_section_" + str(j),
                "start": sub_section_ranges[j][0],
                "end":sub_section_ranges[j][1],
                "offset_1": hex(offset_1),
                "offset_2": hex(offset_2),
                "size":sub_section_size,
                "is_empty": is_empty,
            }
            sub_sections[j] = cur_sub_sect

        section["sub_sections"] = sub_sections
        extracted_sections.append(section)

    for i in range(len(extracted_sections)):
        print(json.dumps((extracted_sections[i]),sort_keys=True, indent=4))

extract_sections('./AIEngineRule_1000000003_20250409.airx')
