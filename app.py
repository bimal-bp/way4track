# Create a form for all tires
with st.form("tire_management_form"):
    st.subheader(f"Tire Details for {selected_tipper} - {tipper_details[selected_tipper]}")
    
    # Create two columns for better layout
    col1, col2 = st.columns(2)
    
    for i, position in enumerate(positions):
        # Alternate between columns
        col = col1 if i % 2 == 0 else col2
        
        with col:
            st.markdown(f"### {position}")
            
            # Get existing data for this position if available
            existing_data = None
            for tire in existing_tires:
                if tire[1] == position:
                    existing_data = tire
                    break
            
            # Tire number (fixed based on position)
            tire_number = f"Tire-{i+1}"
            st.text_input("Tire Number", value=tire_number, key=f"num_{position}", disabled=True)
            
            # Image upload
            uploaded_file = st.file_uploader(
                f"Upload {position} Tire Image",
                type=["jpg", "jpeg", "png"],
                key=f"img_{position}"
            )
            
            # Display existing images if available
            if existing_data and existing_data[2] and len(existing_data[2]) > 0:
                st.write("Existing Images:")
                cols = st.columns(3)
                for idx, img_path in enumerate(existing_data[2]):
                    if os.path.exists(img_path):
                        try:
                            with cols[idx % 3]:
                                image = Image.open(img_path)
                                st.image(image, caption=f"Image {idx+1}", width=150)
                        except:
                            st.warning(f"Could not load image {idx+1}")
            
            # Condition slider
            condition = st.slider(
                "Condition (%)",
                min_value=0, max_value=100, 
                value=existing_data[3] if existing_data else 80,
                key=f"cond_{position}"
            )
            
            # Date installed
            date_installed = st.date_input(
                "Date Installed",
                value=existing_data[4] if existing_data else datetime.now().date(),
                key=f"date_{position}"
            )
            
            # KMR inputs
            col_a, col_b = st.columns(2)
            with col_a:
                starting_kmr = st.number_input(
                    "Starting KMR",
                    min_value=0, 
                    value=existing_data[5] if existing_data else 0,
                    key=f"start_{position}"
                )
            with col_b:
                current_kmr = st.number_input(
                    "Current KMR",
                    min_value=starting_kmr, 
                    value=existing_data[6] if existing_data else starting_kmr,
                    key=f"current_{position}"
                )
            
            st.markdown("---")
