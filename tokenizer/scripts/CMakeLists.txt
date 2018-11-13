SET (SCRIPTS 
        apply_renaming.py
        build_symbol_database.py
        compute_renaming.py
        filter_tokens.py
        json_to_csv.py
        preprocess.py
        tokenize_file.sh)

foreach(_script ${SCRIPTS})
    configure_file(
        "${CMAKE_CURRENT_SOURCE_DIR}/${_script}"
        "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/${_script}"
        COPYONLY)
endforeach()
