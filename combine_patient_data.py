# This will help consolidate all information regarding a patient
from sqlalchemy import create_engine, text
from collections import defaultdict
from datetime import datetime

# manually identified the relevant CSVs and their columns to create a map of csv:columns
# This is later used to extract only those columns from those tables from the local SQLite DB.
# Picked SQLite DB because the given data is relational, easier to load it into SQL-like over No-SQL.
important_details_column_map = defaultdict()
important_details_column_map['allergies'] = ['description','type']
important_details_column_map['conditions'] = ['description']
important_details_column_map['immunizations'] = ['description']
important_details_column_map['medications'] = ['stop','description']
important_details_column_map['observations'] = ['category','description','value','units','type']
important_details_column_map['procedures'] = ['description']
important_details_column_map['patients'] = ['birthdate','gender']


def run_query(query):
    """Runs a given SQL query on the patient data stored in SQLite DB

    Args:
        query (str): Input SQL Query

    Returns:
        list: matched output rows as a list
    """
    engine = create_engine('sqlite:///patient_data.db')
    connection = engine.connect()
    rows = []
    try:
        sql_query = text(query)
        result = connection.execute(sql_query)
        rows = result.fetchall()
        
    except Exception as e:
        print("Error: ", e)
    finally:
        connection.close()
        return rows

def get_patient_per_table_by_id(specific_table, p_id):
    """This helps fetch patient's details from each of the related (relevant) tables.
    Example: This fetches all details of Patient's {Allergy/Condition/etc} given their ID.

    Args:
        specific_table (str): The name of the table to fetch matched rows from
        p_id (_type_): The ID of the patient to fetch details for

    Returns:
        list: Matched rows as per given Table and Patient ID
    """    
    specific_table_columns_to_select = important_details_column_map[specific_table]
    
    SELECT_TABLE_COLUMNS = ', '.join(map(lambda x: f'{"a."}{x}', specific_table_columns_to_select))
    if specific_table == "observations":
        query_to_run = f"""
                SELECT {SELECT_TABLE_COLUMNS}
                FROM patients p
                LEFT JOIN 
                    {specific_table} a ON p.id = a.patient
                WHERE 
                    p.id = '{p_id}'
                    AND a.date = (SELECT MAX(date) 
                                FROM {specific_table} 
                                WHERE patient = '{p_id}');
                """
    else:
        query_to_run = f"""
            SELECT {SELECT_TABLE_COLUMNS}
            FROM patients p
            LEFT JOIN {specific_table} a ON p.id = a.patient
                        WHERE p.id = '{p_id}';
        """
        
    
    query_result = run_query(query_to_run)
    return query_result

def get_patient_details(p_id):
    """Get patient details, birthdate and gender.

    Args:
        p_id (str): ID of the patient

    Returns:
        list: Matched row
    """    
    patients_table_columns_to_select = important_details_column_map['patients']
    SELECT_PATIENTS_COLUMNS = ', '.join(map(lambda x: f'{"p."}{x}', patients_table_columns_to_select))
    patient_query = f"""
            SELECT {SELECT_PATIENTS_COLUMNS}
            FROM patients p
            WHERE p.id = '{p_id}';
            """ 
    
    query_result = run_query(patient_query)
    return query_result

def get_all_patient_ids():
    """Gets all patient IDs in the SQLite DB

    Returns:
        list : Fetches all patient IDs
    """    
    patient_query = f"""
            SELECT id
            FROM patients;
            """ 
    
    query_result = run_query(patient_query)
    return query_result

def calculate_age(date_string):
    """Calculates age given a date of birth

    Args:
        date_string (str): Date in YYYY-MM-DD

    Returns:
        int: Age in years
    """    
    # Example birthdate (in standard Python date format)
    birthdate = datetime.strptime(date_string, "%Y-%m-%d")

    # Get the current date
    current_date = datetime.now()

    # Calculate the difference in years
    age = current_date.year - birthdate.year

    # Adjust if the birthday hasn't occurred yet this year
    if (current_date.month, current_date.day) < (birthdate.month, birthdate.day):
        age -= 1
    return age

def create_patient_profile(p_id):
    """Generates a patient profile combining all important fields

    Args:
        p_id (str): Patient ID

    Returns:
        dict: dict with the details, age, gender, ID
    """    
    patient_profile = defaultdict()
    patient_details = get_patient_details(p_id)
    patient_bday = patient_details[0][0]
    age = calculate_age(patient_bday)

    for key in important_details_column_map.keys():
        if key != 'patients': 
            patient_profile[key] = get_patient_per_table_by_id(key, p_id)
    
    return {f"{p_id}":{
                        "age": age,
                        "gender": patient_details[0][1],
                        "profile":patient_profile
                    }
            }

def main():
    print(create_patient_profile('339144f8-50e1-633e-a013-f361391c4cff'))

if __name__ == "__main__":
    main()
