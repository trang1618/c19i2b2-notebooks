import re
import glob
import pandas as pd
import numpy as np
import datetime
import dateutil.parser
from os.path import join


from constants import (
    COLUMNS,
    DATA_DIR,
    LOOKUP_DATA_DIR,
    LAB_ADDITIONAL_DATA_DIR,
    SITE_DATA_GLOB, 
    SITE_FILE_REGEX,
    COMBINED_DATA_GLOB,
    COMBINED_DATA_REGEX,
    COMBINED_COUNTRY_LEVEL_DATA_REGEX,
    COMBINED_SITE_LEVEL_DATA_REGEX,
    SITE_FILE_TYPES,
    ALL_SITE_FILE_TYPES,
    DATA_AGGREGATE_TYPES
)

"""
Utilities for listing site file information.
"""
def get_site_file_paths():
    return glob.glob(SITE_DATA_GLOB)

def get_site_file_info(file_types=ALL_SITE_FILE_TYPES):
    file_paths = get_site_file_paths()
    potential_matches = [ 
        (re.match(SITE_FILE_REGEX.format(file_type=ft), fp), ft)
            for ft in file_types 
            for fp in file_paths 
    ]
    all_info = [ dict(**m.groupdict(), file_type=ft, file_path=m[0]) for m, ft in potential_matches if m is not None ]
    for info in all_info:
        info["date"] = datetime.date(int(info["year"]), int(info["month"]), int(info["day"]))
    return all_info

def get_site_ids(file_types=ALL_SITE_FILE_TYPES):
    all_site_file_info = get_site_file_info(file_types=file_types)
    return list(set([ info["site_id"] for info in all_site_file_info ]))

def get_latest_site_file_info(file_types=ALL_SITE_FILE_TYPES):
    # For each site ID, only get the latest info dict for each site file type
    all_site_file_info = get_site_file_info(file_types=file_types)
    sorted_site_file_info = sorted(all_site_file_info, key=lambda info: (info["site_id"], info["file_type"], info["date"]), reverse=True)
    unique_site_file_info = dict()
    for info in sorted_site_file_info:
        key = (info["site_id"], info["file_type"])
        if key not in unique_site_file_info:
            unique_site_file_info[key] = info
    return list(unique_site_file_info.values())

def get_site_file_info_by_date(year, month, day, file_types=ALL_SITE_FILE_TYPES):
    target_date = datetime.date(year, month, day)
    all_site_file_info = get_site_file_info(file_types=file_types)
    return [ info for info in all_site_file_info if info["date"] == target_date ]

"""
Utilities for reading in data from a list of site info for each file type.
"""
def read_full_site_df(site_file_info, file_type, columns):
    filtered_site_file_info = [ info for info in site_file_info if info["file_type"] == file_type ]

    site_dfs = []
    for info in filtered_site_file_info:
        df = pd.read_csv(info["file_path"], header=None)
        if df.shape[0] > 0 and df.iloc[0,0].lower() in [ "site_id", "siteid" ]:
            # This file has a header but should not have one.
            df = df.drop(index=[0])
        site_dfs.append(df)

    full_df = pd.concat(site_dfs, ignore_index=True)
    full_df = full_df.rename(columns=dict(zip(range(len(columns)), columns)))
    return full_df

def read_full_daily_counts_df(site_file_info):
    df = read_full_site_df(site_file_info, SITE_FILE_TYPES.DAILY_COUNTS, [
        COLUMNS.SITE_ID,
        COLUMNS.DATE,
        COLUMNS.NEW_POSITIVE_CASES,
        COLUMNS.PATIENTS_IN_ICU,
        COLUMNS.NEW_DEATHS
    ])
    df[COLUMNS.DATE] = df[COLUMNS.DATE].astype(str)
    def convert_date(date_str):
        try:
            return dateutil.parser.parse(date_str)
        except:
            return np.nan
    df[COLUMNS.DATE] = df[COLUMNS.DATE].apply(convert_date)
    df[COLUMNS.NEW_POSITIVE_CASES] = df[COLUMNS.NEW_POSITIVE_CASES].astype(int)
    df[COLUMNS.PATIENTS_IN_ICU] = df[COLUMNS.PATIENTS_IN_ICU].astype(int)
    df[COLUMNS.NEW_DEATHS] = df[COLUMNS.NEW_DEATHS].astype(int)
    return df

def read_full_demographics_df(site_file_info):
    df = read_full_site_df(site_file_info, SITE_FILE_TYPES.DEMOGRAPHICS, [
        COLUMNS.SITE_ID,
        COLUMNS.SEX,
        COLUMNS.TOTAL_PATIENTS,
        COLUMNS.AGE_0TO2,
        COLUMNS.AGE_3TO5,
        COLUMNS.AGE_6TO11,
        COLUMNS.AGE_12TO17,
        COLUMNS.AGE_18TO25,
        COLUMNS.AGE_26TO49,
        COLUMNS.AGE_50TO69,
        COLUMNS.AGE_70TO79,
        COLUMNS.AGE_80PLUS
    ])
    df[COLUMNS.TOTAL_PATIENTS] = df[COLUMNS.TOTAL_PATIENTS].astype(int)
    return df

def read_full_diagnoses_df(site_file_info):
    df = read_full_site_df(site_file_info, SITE_FILE_TYPES.DIAGNOSES, [
        COLUMNS.SITE_ID,
        COLUMNS.ICD_CODE,
        COLUMNS.ICD_VERSION,
        COLUMNS.NUM_PATIENTS
    ])
    df[COLUMNS.NUM_PATIENTS] = df[COLUMNS.NUM_PATIENTS].astype(int)
    return df

def read_full_labs_df(site_file_info):
    df = read_full_site_df(site_file_info, SITE_FILE_TYPES.LABS, [
        COLUMNS.SITE_ID,
        COLUMNS.LOINC,
        COLUMNS.DAYS_SINCE_POSITIVE,
        COLUMNS.NUM_PATIENTS,
        COLUMNS.MEAN_VALUE,
        COLUMNS.STDEV_VALUE
    ])
    df[COLUMNS.NUM_PATIENTS] = df[COLUMNS.NUM_PATIENTS].astype(int)
    df[COLUMNS.DAYS_SINCE_POSITIVE] = df[COLUMNS.DAYS_SINCE_POSITIVE].astype(int)
    df[COLUMNS.MEAN_VALUE] = df[COLUMNS.MEAN_VALUE].astype(float)
    df[COLUMNS.STDEV_VALUE] = df[COLUMNS.STDEV_VALUE].astype(float)
    return df

"""
Helpers for reading all of the latest data for each site file type.
"""
def read_latest_daily_counts_df():
    return read_full_daily_counts_df(get_latest_site_file_info())

def read_latest_demographics_df():
    return read_full_demographics_df(get_latest_site_file_info())

def read_latest_diagnoses_df():
    return read_full_diagnoses_df(get_latest_site_file_info())

def read_latest_labs_df():
    return read_full_labs_df(get_latest_site_file_info())

"""
Helpers for reading combined datasets.
"""
def get_combined_file_paths():
    return glob.glob(COMBINED_DATA_GLOB)

def read_combined_file_df(ft=SITE_FILE_TYPES.DEMOGRAPHICS, agg=DATA_AGGREGATE_TYPES.COMBINED_ALL):
    file_paths = get_combined_file_paths()

    regex = COMBINED_DATA_REGEX
    if agg == DATA_AGGREGATE_TYPES.COMBINED_BY_COUNTRY:
        regex = COMBINED_COUNTRY_LEVEL_DATA_REGEX
    elif agg == DATA_AGGREGATE_TYPES.COMBINED_BY_SITE:
        regex = COMBINED_SITE_LEVEL_DATA_REGEX

    potential_matches = [
        (re.match(regex.format(file_type=ft), fp), ft)
            for fp in file_paths
    ]
    all_file_info = [ dict(**m.groupdict(), file_type=ft, file_path=m[0]) for m, ft in potential_matches if m is not None ]
    if len(all_file_info) != 1:
        print("there is more than one combined files per type")
        return None
    file_info = all_file_info[0]

    columns = get_combined_columns(ft)
    df = pd.read_csv(file_info["file_path"])
    df = df.rename(columns=dict(zip(range(len(columns)), columns)))
    return df

def read_combined_daily_counts_df():
    return read_combined_file_df(ft=SITE_FILE_TYPES.DAILY_COUNTS)

def read_combined_demographics_df():
    return read_combined_file_df(ft=SITE_FILE_TYPES.DEMOGRAPHICS)

def read_combined_diagnoses_df():
    return read_combined_file_df(ft=SITE_FILE_TYPES.DIAGNOSES)

def read_combined_labs_df():
    return read_combined_file_df(ft=SITE_FILE_TYPES.LABS)

def read_combined_by_country_daily_counts_df():
    return read_combined_file_df(ft=SITE_FILE_TYPES.DAILY_COUNTS, agg=DATA_AGGREGATE_TYPES.COMBINED_BY_COUNTRY)

def read_combined_by_country_demographics_df():
    return read_combined_file_df(ft=SITE_FILE_TYPES.DEMOGRAPHICS, agg=DATA_AGGREGATE_TYPES.COMBINED_BY_COUNTRY)

def read_combined_by_country_diagnoses_df():
    return read_combined_file_df(ft=SITE_FILE_TYPES.DIAGNOSES, agg=DATA_AGGREGATE_TYPES.COMBINED_BY_COUNTRY)

def read_combined_by_country_labs_df():
    return read_combined_file_df(ft=SITE_FILE_TYPES.LABS, agg=DATA_AGGREGATE_TYPES.COMBINED_BY_COUNTRY)

def read_combined_by_site_daily_counts_df():
    return read_combined_file_df(ft=SITE_FILE_TYPES.DAILY_COUNTS, agg=DATA_AGGREGATE_TYPES.COMBINED_BY_SITE)

def read_combined_by_site_demographics_df():
    return read_combined_file_df(ft=SITE_FILE_TYPES.DEMOGRAPHICS, agg=DATA_AGGREGATE_TYPES.COMBINED_BY_SITE)

def read_combined_by_site_diagnoses_df():
    return read_combined_file_df(ft=SITE_FILE_TYPES.DIAGNOSES, agg=DATA_AGGREGATE_TYPES.COMBINED_BY_SITE)

def read_combined_by_site_labs_df():
    return read_combined_file_df(ft=SITE_FILE_TYPES.LABS, agg=DATA_AGGREGATE_TYPES.COMBINED_BY_SITE)

"""
Helpers for reading additional data files.
"""
def read_icd_df():
    return pd.read_csv(join(LOOKUP_DATA_DIR, "icd_table.txt"), sep="\t", header=0)

def read_loinc_df():
    return pd.read_csv(join(LOOKUP_DATA_DIR, "lab_table.txt"), sep="\t", header=0)

def read_lab_meta_ci_df():
    return pd.read_csv(join(LAB_ADDITIONAL_DATA_DIR, "Lab_MetaCI_ran.csv"), sep=",", header=0)

def read_lab_nprop_time_df():
    return pd.read_csv(join(LAB_ADDITIONAL_DATA_DIR, "Lab_nprop_time.csv"), sep=",", header=0)

def read_lab_variation_by_country_df():
    return pd.read_csv(join(LAB_ADDITIONAL_DATA_DIR, "Lab_VariationByCountry.csv"), sep=",", header=0)

def read_lab_weights_df():
    return pd.read_csv(join(LAB_ADDITIONAL_DATA_DIR, "Lab_weights_for_MetaAnalysis.csv"), sep=",", header=0)

def read_site_details_df():
    details_df = pd.read_csv(join(DATA_DIR, "Health_Systems_Participating.csv"), sep=",", header=0)
    id_df = pd.read_csv(join(DATA_DIR, "SiteID_Map.csv"), sep=",", header=0)
    details_df = details_df.set_index("Acronym")
    id_df = id_df.set_index("Acronym")

    details_df = details_df.join(id_df)
    return details_df

def get_siteid_anonymous_map():
    df = read_site_details_df()
    df = df.reset_index()
    return dict(zip(df["Acronym"].values.tolist(), df["Anonymous Site ID"].values.tolist()))

def get_siteid_country_map():
    df = read_site_details_df()
    df = df.reset_index()
    return dict(zip(df["Acronym"].values.tolist(), df["Country"].values.tolist()))

def get_siteid_color_maps():
    df = read_site_details_df()
    df = df.reset_index()
    site_map = dict(zip(df["Acronym"].values.tolist(), df["Site Color"].values.tolist()))
    site_country_map = dict(zip(df["Acronym"].values.tolist(), df["Country Color"].values.tolist()))
    site_combined_map = dict(zip(df["Acronym"].values.tolist(), df["Combined Color"].values.tolist()))
    return site_map, site_country_map, site_combined_map

def get_anonymousid_color_maps():
    df = read_site_details_df().sort_values(by=["Anonymous Site ID"])
    df = df.reset_index()
    anonymousid_map = dict(zip(df["Anonymous Site ID"].values.tolist(), df["Site Color"].values.tolist()))
    anonymousid_country_map = dict(zip(df["Anonymous Site ID"].values.tolist(), df["Country Color"].values.tolist()))
    anonymousid_combined_map = dict(zip(df["Anonymous Site ID"].values.tolist(), df["Combined Color"].values.tolist()))
    return anonymousid_map, anonymousid_country_map, anonymousid_combined_map

def get_country_color_map():
    df = read_site_details_df()
    df = df.reset_index()
    df = df.drop_duplicates(subset=["Country"])
    return dict(zip(df["Country"].values.tolist(), df["Country Color"].values.tolist()))

def get_combined_color():
    return "#444444"

"""
Helpers to make columns by data types.
"""
def get_combined_columns(filetype):
    if filetype == SITE_FILE_TYPES.DAILY_COUNTS:
        return [
            COLUMNS.SITE_ID,
            COLUMNS.DATE,
            COLUMNS.NEW_POSITIVE_CASES,
            COLUMNS.PATIENTS_IN_ICU,
            COLUMNS.NEW_DEATHS,
            COLUMNS.UNMASKED_SITES_NEW_POSITIVE_CASES,
            COLUMNS.UNMASKED_SITES_PATIENTS_IN_ICU,
            COLUMNS.UNMASKED_SITES_NEW_DEATHS,
            COLUMNS.MASKED_SITES_NEW_POSITIVE_CASES,
            COLUMNS.MASKED_SITES_PATIENTS_IN_ICU,
            COLUMNS.MASKED_SITES_NEW_DEATHS,
            COLUMNS.MASKED_UPPER_BOUND_NEW_POSITIVE_CASES,
            COLUMNS.MASKED_UPPER_BOUND_PATIENTS_IN_ICU,
            COLUMNS.MASKED_UPPER_BOUND_NEW_DEATHS
        ]
    elif filetype == SITE_FILE_TYPES.DEMOGRAPHICS:
        return [
            COLUMNS.SITE_ID,
            COLUMNS.SEX,
            COLUMNS.TOTAL_PATIENTS,
            COLUMNS.AGE_0TO2,
            COLUMNS.AGE_3TO5,
            COLUMNS.AGE_6TO11,
            COLUMNS.AGE_12TO17,
            COLUMNS.AGE_18TO25,
            COLUMNS.AGE_26TO49,
            COLUMNS.AGE_50TO69,
            COLUMNS.AGE_70TO79,
            COLUMNS.AGE_80PLUS,
            COLUMNS.UNMASKED_SITES_TOTAL_PATIENTS,
            COLUMNS.UNMASKED_SITES_AGE_0TO2,
            COLUMNS.UNMASKED_SITES_AGE_3TO5,
            COLUMNS.UNMASKED_SITES_AGE_6TO11,
            COLUMNS.UNMASKED_SITES_AGE_12TO17,
            COLUMNS.UNMASKED_SITES_AGE_18TO25,
            COLUMNS.UNMASKED_SITES_AGE_26TO49,
            COLUMNS.UNMASKED_SITES_AGE_50TO69,
            COLUMNS.UNMASKED_SITES_AGE_70TO79,
            COLUMNS.UNMASKED_SITES_AGE_80PLUS,
            COLUMNS.MASKED_SITES_TOTAL_PATIENTS,
            COLUMNS.MASKED_SITES_AGE_0TO2,
            COLUMNS.MASKED_SITES_AGE_3TO5,
            COLUMNS.MASKED_SITES_AGE_6TO11,
            COLUMNS.MASKED_SITES_AGE_12TO17,
            COLUMNS.MASKED_SITES_AGE_18TO25,
            COLUMNS.MASKED_SITES_AGE_26TO49,
            COLUMNS.MASKED_SITES_AGE_50TO69,
            COLUMNS.MASKED_SITES_AGE_70TO79,
            COLUMNS.MASKED_SITES_AGE_80PLUS,
            COLUMNS.MASKED_UPPER_BOUND_TOTAL_PATIENTS,
            COLUMNS.MASKED_UPPER_BOUND_AGE_0TO2,
            COLUMNS.MASKED_UPPER_BOUND_AGE_3TO5,
            COLUMNS.MASKED_UPPER_BOUND_AGE_6TO11,
            COLUMNS.MASKED_UPPER_BOUND_AGE_12TO17,
            COLUMNS.MASKED_UPPER_BOUND_AGE_18TO25,
            COLUMNS.MASKED_UPPER_BOUND_AGE_26TO49,
            COLUMNS.MASKED_UPPER_BOUND_AGE_50TO69,
            COLUMNS.MASKED_UPPER_BOUND_AGE_70TO79,
            COLUMNS.MASKED_UPPER_BOUND_AGE_80PLUS
        ]
    elif filetype == SITE_FILE_TYPES.DIAGNOSES:
        return [
            COLUMNS.SITE_ID,
            COLUMNS.ICD_CODE,
            COLUMNS.ICD_VERSION,
            COLUMNS.NUM_PATIENTS,
            COLUMNS.MASKED_SITES_NUM_PATIENTS,
            COLUMNS.MASKED_UPPER_BOUND_NUM_PATIENTS,
        ]
    elif filetype == SITE_FILE_TYPES.LABS:
        return [
            COLUMNS.SITE_ID,
            COLUMNS.LOINC,
            COLUMNS.DAYS_SINCE_POSITIVE,
            COLUMNS.NUM_PATIENTS,
            COLUMNS.MEAN_VALUE,
            COLUMNS.STDEV_VALUE,
            COLUMNS.UNMASKED_SITES_NUM_PATIENTS,
            COLUMNS.MASKED_SITES_NUM_PATIENTS,
            COLUMNS.MASKED_UPPER_BOUND_NUM_PATIENTS
        ]

"""
Utilities to customize visualizations.
"""
def apply_theme(
    base,
    title_anchor="start",
    title_font_size=18,
    axis_title_font_size=16,
    axis_label_font_size=14,
    legend_orient="top-left",
    legend_stroke_color="lightgray",
    legend_padding=10,
    label_font_size=14
):
    return base.configure_view(
        # ...
    ).configure_header(
        titleFontSize=16,
        titleFontWeight=300,
        labelFontSize=13
    ).configure_title(
        fontSize=title_font_size,
        fontWeight=400,
        anchor=title_anchor,
        align="left"
    ).configure_axis(
        labelFontSize=axis_label_font_size,
        labelFontWeight=300,
        titleFontSize=axis_title_font_size,
        titleFontWeight=300,
        labelLimit=1000,
        labelAngle=0
    ).configure_legend(
        titleFontSize=16, titleFontWeight=400,
        labelFontSize=label_font_size, labelFontWeight=300,
        padding=legend_padding,
        cornerRadius=0,
        orient=legend_orient,
        fillColor="white",
        strokeColor=legend_stroke_color
    ).configure_concat(
        spacing=0
    )