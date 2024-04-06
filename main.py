import csv, argparse, os
from pathlib import Path
from datetime import datetime

import pandas as pd
from PyPDF2 import PdfReader


# Configurando parser dos parâmetros de entrada
parser = argparse.ArgumentParser(description="")
parser.add_argument(
    "dir", 
    help="Pasta que contém os arquivos a serem processados"
)
parser.add_argument(
    "--lib",
    default="ID_LIBRARY_TMS.xlsx", 
    help="Arquivo dentro da pasta templates a ser usado como biblioteca. Default: ID_LIBRARY_GDM.xlsx"
)


def get_number_of_identifications(line: str):
    if "Number of Identifications" in line:
        n = line.split(' ')[3].strip()
        return int(n)
    else:
        return None


def extract_useful_info(line):
    splitted = line.split(' ', maxsplit=1)

    data = {
        "RT": splitted[0],
        "chemical_name": splitted[1].replace('?', '').strip()
    }
    return data


def should_skip_line(line: str):
    if line.startswith("AMDIS GC/MS Analysis Report"):
        return True
    elif  line.startswith("Library:"):
        return True
    elif  line.startswith("Data:"):
        return True
    elif "RT(min)" in line:
        return True
    else:
        return False


def reached_end(line: str):
    if line.startswith("QA/QC:"):
        return True
    else:
        return False


def correct_page_bug(line: str):
    if "Page" in line:
        _line = line.split("Page ")[-1]
        return _line[4:].strip()
    

# Match com a biblioteca
def fnc_clear_chemical_name(chemical_name: str):
    if chemical_name.startswith("RI") or chemical_name.startswith("contamination"):
        return chemical_name.replace(" ", "")
    else:        
        chemical_name = chemical_name.split("_VAR5_ALK_")[-1]
        chemical_name = chemical_name.split("(ID#:")[0]

        if ", " in chemical_name:
            chemical_name = "".join(chemical_name.split(", ")[::-1])
        return chemical_name.replace(" ", "")

def find_matching_name(chemical_name, lib):
    candidates = []
    for idx, item in enumerate(lib):
        if item["id_match"].lower() in chemical_name.lower():
            candidates.append(idx)
    
    if len(candidates) == 1:
        idx = candidates[0]
        return lib[idx]
    

if __name__ == "__main__":

    #  args = parser.parse_args(['exemplo_2'])
    args = parser.parse_args()

    # Variáveis iniciais
    now = datetime.now()

    BASE_DIR = Path(__file__).resolve().parent

    RAW_DIR = BASE_DIR / 'raw_files'
    TEMPLATE_DIR = BASE_DIR / 'templates'

    BASE_OUTPUT_DIR = BASE_DIR / 'processed_files' 
    if BASE_OUTPUT_DIR.is_dir() is False:
        os.mkdir(BASE_OUTPUT_DIR)

    LIB_FILE = args.lib
    LIB_PATH = TEMPLATE_DIR / LIB_FILE

    FILE_DIR = RAW_DIR / args.dir

    filenames = []
    trusted_lines = {}
    # for filename in filenames:
        # file_path = RAW_DIR / (filename + '.pdf')
    for filename in os.listdir(FILE_DIR):
        file_path = FILE_DIR / filename
        filenames.append(filename)

        reader = PdfReader(file_path)
        processed_lines = []

        total_expected = None
        for idx_pg, page in enumerate(reader.pages):
            txt = page.extract_text()

            last_line = ''
            for idx, line in enumerate(txt.split("\n")):
                if reached_end(line):
                    break

                if idx_pg > 0 and idx == 1:
                    line = correct_page_bug(line)

                if should_skip_line(line):
                    continue

                if total_expected is None:
                    total_expected = get_number_of_identifications(line)
                    continue
            
                if last_line is None:
                    last_line = ''

                if line.startswith("RI =") and "RI-RI" in line:  # Ended at last line
                    last_line += line
                    last_line = ' '.join([word for word in last_line.split(' ') if word != ''])
                    processed_lines.append(last_line)
                    last_line = None
                elif "ID#:" in line and line.strip().endswith(")"): # Ended at current line
                    last_line += line.strip()
                    last_line = ' '.join([word for word in last_line.split(' ') if word != ''])
                    processed_lines.append(last_line)
                    last_line = None
                else:
                    last_line += line.strip()
                
                print(f"Linha {idx:0>3} - {line}")


        if len(processed_lines) == total_expected:
            print("Deu boa! Total de amostras esperado coincidiu com o total de amostras encontrado!")
            print("Total esperado de linhas:", total_expected)
        else:
            print("Deu ruim, acho bom conferir o arquivo", filename)
            print("Total esperado:", total_expected)
            print("Total encontrado:", len(processed_lines))


        for idx, line in enumerate(processed_lines):
            data = extract_useful_info(line)
            print(f"Linha {idx:0>3} - {len(trusted_lines)} -{data['chemical_name']}")
            try:
                trusted_lines[data['chemical_name']]["chemical_name"] = data['chemical_name']
                trusted_lines[data['chemical_name']][filename] = str(data['RT']).replace('.', ',')
            except KeyError:
                trusted_lines[data['chemical_name']] = {
                    "chemical_name": data['chemical_name'],
                    filename: str(data['RT']).replace('.', ','),
                }

    refined_data = []
    for chemical, data in trusted_lines.items():
        refined_data.append(data)

    df = pd.DataFrame(refined_data, dtype=str)

    OUTPUT_DIR = BASE_OUTPUT_DIR / now.strftime(args.dir + ' %d%m%Y %H-%M-%S.csv')
    if OUTPUT_DIR.is_dir() is False:
        os.mkdir(OUTPUT_DIR)

    output_file = OUTPUT_DIR / now.strftime('parcial %d%m%Y %H-%M-%S.csv')
    df.to_csv(output_file, index=False, sep=";", quoting=csv.QUOTE_ALL)

    df["name_match"] = df["chemical_name"].apply(fnc_clear_chemical_name)
    # df[["chemical_name", "name_match"]].to_csv(OUTPUT_DIR / 'olhe.csv', index=False)

    lib = pd.read_excel(LIB_PATH, header=None, skiprows=1, names=["RI", "identity", "class", "m/z (1)", "m/z (2)", "m/z (3)", "comments"], dtype=str, keep_default_na=False)
    lib["id_match"] = lib["identity"].str.replace(' ', '')

    new_refined_data = df.to_dict("records")
    refined_lib = lib.to_dict("records")

    for i, row in enumerate(new_refined_data):
        chemical_name = row["name_match"]
        found_data = find_matching_name(chemical_name, refined_lib)
        if found_data is not None:
            new_refined_data[i] = {**row, **found_data}

    df_final = pd.DataFrame(new_refined_data, dtype=str)

    final_cols = df_final.columns
    float_filenames = [_file + '_float' for _file in filenames]

    for float_col, col in zip(float_filenames, filenames):
        df_final[float_col] = df_final[col].str.replace(',', '.').astype(float)

    df_final["RI"] = df_final["RI"].str.replace(".", ",")
    # columns = df.columns + ["RI", "identity", "class", "m/z (1)", "m/z (2)", "m/z (3)"]
    # df_final = df_final[columns]

    final_file = OUTPUT_DIR / now.strftime('final %d%m%Y %H-%M-%S.csv')

    df_final = df_final.sort_values(float_filenames)
    df_final[final_cols].to_csv(final_file, index=False, sep=";", quoting=csv.QUOTE_ALL)

