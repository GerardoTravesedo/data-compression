import os


def get_compressed_output_path(input_path, output_path):
    input_file = os.path.basename(input_path)

    output_folder = os.path.dirname(output_path)

    # If output path is an existing folder, then use it and add a file with the same name as input_path
    # with extension .huff
    if os.path.exists(output_path) and os.path.isdir(output_path):
        return "{}/{}.{}".format(output_path, os.path.splitext(input_file)[0], "huff")
    # If output path contains valid folders and a file with .huff extension, then use it
    elif os.path.exists(output_folder) and os.path.isdir(output_folder) and os.path.splitext(output_path)[1] is ".huff":
        return output_path
    else:
        raise ValueError("Invalid output path: {}. Either provide an existing folder or a "
                         "file with extension .huff".format(output_path))


def get_decompressed_output_path(input_path, output_path):
    input_file = input_path.split('/')[-1]
    output_folder = "." if "/" not in output_path else os.path.dirname(output_path)

    # If output path is a folder that exists with no file name, put the decompressed file there and name
    # it as the input one without the extension
    if os.path.exists(output_path) and os.path.isdir(output_path):
        return "{}/{}".format(output_path, os.path.splitext(input_file)[0])
    # If provided output path contains folders and file, then use it
    elif os.path.exists(output_folder) and os.path.isdir(output_folder):
        return output_path
    else:
        raise ValueError("Invalid output path: {}. Path doesn't exist".format(output_path))
