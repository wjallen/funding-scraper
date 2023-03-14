from fuzzywuzzy import fuzz

def fuzzy_match(logging, last_name, name_dict, found_worksheet,
                not_found_worksheet, award_full_name,
                base_info, workbook, f_row, nf_row):
    """
    Given a search results award PI name, fuzzy match against each entry in
    the TACC userlist database. Accept matches in two categories--80-88% and 89+%.
    """
    f_format = workbook.add_format({'bg_color': '#90EE90'})
    nf_format = workbook.add_format({'bg_color': '#FCC981'})
    for key, values in name_dict.items():
        # Last name MUST match exactly
        if last_name.capitalize() == values[2].capitalize():
            match_percent = fuzz.ratio(award_full_name, key)
            # If first name 89+% match, add it to found and highlight green
            if match_percent >= 89:
                logging.info(f"{award_full_name} fuzzy matches {values[1:2]} \
                               --match percent = {match_percent}")
                found_worksheet.write_row(f_row, 0, [values[0], values[1], values[2]]
                                          + base_info
                                          + [f"match percent = {match_percent}"], f_format)
                return True
            # If first name 80+% match, add it to found and highlight orange
            elif match_percent >= 80:
                logging.info(f"{award_full_name} fuzzy matches {values[1:2]} \
                               --match percent = {match_percent}")
                # Log and color the field in orange
                found_worksheet.write_row(f_row, 0, [values[0], values[1], values[2]]
                                          + base_info
                                          + [f"match percent = {match_percent}"], nf_format)
                return True
    # If no matches >=80%, add to not found workbook
    logging.info(f"{award_full_name} has no match")
    not_found_worksheet.write_row(nf_row, 0, base_info)
    return False

