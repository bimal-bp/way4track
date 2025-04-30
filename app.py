import streamlit as st
from PIL import Image
import os
import pandas as pd

# Initialize session state for tire data
if 'tires' not in st.session_state:
    st.session_state.tires = pd.DataFrame(columns=[
        'Tipper ID', 
        'Tire Number', 
        'Position', 
        'Image Path', 
        'Condition (%)', 
        'Date Installed',
        'Current KM',
        'Last Checked'
    ])

# Create directories if they don't exist
os.makedirs("tire_images", exist_ok=True)

# App title
st.title("Tipper Tire Management System")
st.subheader("Track and manage tires across your fleet of 9 tippers")

# Sidebar for navigation
menu = st.sidebar.selectbox(
    "Menu",
    ["Add/Update Tire", "View All Tires", "Tire Dashboard", "Delete Tire"]
)

if menu == "Add/Update Tire":
    st.header("Add or Update Tire Information")
    
    # Form for tire details
    with st.form("tire_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            tipper_id = st.selectbox(
                "Tipper ID", 
                options=[f"Tipper-{i}" for i in range(1, 10)],
                index=0
            )
            
            tire_number = st.selectbox(
                "Tire Number", 
                options=[f"Tire-{i}" for i in range(1, 11)],
                index=0
            )
            
            position_options = [
                "Front Left", "Front Right",
                "Middle Left 1", "Middle Right 1",
                "Middle Left 2", "Middle Right 2",
                "Rear Left 1", "Rear Right 1",
                "Rear Left 2", "Rear Right 2"
            ]
            position = st.selectbox(
                "Position", 
                options=position_options,
                index=0
            )
            
        with col2:
            condition = st.slider("Condition (%)", 0, 100, 80)
            date_installed = st.date_input("Date Installed")
            current_km = st.number_input("Current KM Running", min_value=0, step=1000)
            image_file = st.file_uploader("Upload Tire Image", type=["jpg", "png", "jpeg"])
        
        submitted = st.form_submit_button("Save Tire")
        
        if submitted:
            # Handle image upload
            image_path = None
            if image_file is not None:
                image_path = f"tire_images/{tipper_id}_{tire_number}.{image_file.name.split('.')[-1]}"
                with open(image_path, "wb") as f:
                    f.write(image_file.getbuffer())
            
            # Check if this tire already exists for this tipper
            existing_idx = st.session_state.tires[
                (st.session_state.tires['Tipper ID'] == tipper_id) & 
                (st.session_state.tires['Tire Number'] == tire_number)
            ].index
            
            if not existing_idx.empty:
                # Update existing tire
                idx = existing_idx[0]
                st.session_state.tires.at[idx, 'Position'] = position
                st.session_state.tires.at[idx, 'Condition (%)'] = condition
                st.session_state.tires.at[idx, 'Date Installed'] = date_installed
                st.session_state.tires.at[idx, 'Current KM'] = current_km
                if image_path:
                    st.session_state.tires.at[idx, 'Image Path'] = image_path
                st.session_state.tires.at[idx, 'Last Checked'] = pd.Timestamp.now()
                st.success(f"Tire {tire_number} on {tipper_id} updated successfully!")
            else:
                # Add new tire
                new_tire = {
                    'Tipper ID': tipper_id,
                    'Tire Number': tire_number,
                    'Position': position,
                    'Image Path': image_path,
                    'Condition (%)': condition,
                    'Date Installed': date_installed,
                    'Current KM': current_km,
                    'Last Checked': pd.Timestamp.now()
                }
                st.session_state.tires = st.session_state.tires.append(new_tire, ignore_index=True)
                st.success(f"Tire {tire_number} added to {tipper_id} successfully!")

elif menu == "View All Tires":
    st.header("All Tires Information")
    
    if st.session_state.tires.empty:
        st.warning("No tires added yet!")
    else:
        # Filter by tipper if desired
        selected_tipper = st.selectbox(
            "Filter by Tipper (or view all)",
            options=["All"] + [f"Tipper-{i}" for i in range(1, 10)]
        )
        
        if selected_tipper != "All":
            display_tires = st.session_state.tires[st.session_state.tires['Tipper ID'] == selected_tipper]
        else:
            display_tires = st.session_state.tires
        
        # Display filtered tires in a table
        st.dataframe(display_tires)
        
        # Show details for selected tire
        if not display_tires.empty:
            selected_tire = st.selectbox(
                "Select a tire to view details",
                options=display_tires.apply(
                    lambda x: f"{x['Tipper ID']} - {x['Tire Number']}", 
                    axis=1
                ).unique()
            )
            
            tipper_id, tire_num = selected_tire.split(" - ")
            tire_data = st.session_state.tires[
                (st.session_state.tires['Tipper ID'] == tipper_id) & 
                (st.session_state.tires['Tire Number'] == tire_num)
            ].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"Tipper: {tipper_id}")
                st.subheader(f"Tire: {tire_num}")
                st.write(f"**Position:** {tire_data['Position']}")
                st.write(f"**Condition:** {tire_data['Condition (%)']}% remaining")
                st.write(f"**Date Installed:** {tire_data['Date Installed']}")
                st.write(f"**Current KM:** {tire_data['Current KM']:,} km")
                st.write(f"**Last Checked:** {tire_data['Last Checked']}")
                
            with col2:
                if tire_data['Image Path'] and os.path.exists(tire_data['Image Path']):
                    try:
                        image = Image.open(tire_data['Image Path'])
                        st.image(image, caption=f"{tipper_id} - {tire_num} Image", width=300)
                    except:
                        st.warning("Could not load image")
                else:
                    st.warning("No image available for this tire")

elif menu == "Tire Dashboard":
    st.header("Tire Condition Dashboard")
    
    if st.session_state.tires.empty:
        st.warning("No tires added yet!")
    else:
        # Filter by tipper if desired
        selected_tipper = st.selectbox(
            "View Dashboard for Tipper (or view all)",
            options=["All"] + [f"Tipper-{i}" for i in range(1, 10)]
        )
        
        if selected_tipper != "All":
            display_tires = st.session_state.tires[st.session_state.tires['Tipper ID'] == selected_tipper]
        else:
            display_tires = st.session_state.tires
        
        # Display condition summary
        st.subheader("Condition Summary")
        st.bar_chart(display_tires.set_index(['Tipper ID', 'Tire Number'])['Condition (%)'])
        
        # Show tires that need attention (condition < 30%)
        critical_tires = display_tires[display_tires['Condition (%)'] < 30]
        if not critical_tires.empty:
            st.warning("The following tires need immediate attention:")
            st.dataframe(critical_tires[['Tipper ID', 'Tire Number', 'Position', 'Condition (%)', 'Current KM']])
        else:
            st.success("All tires are in good condition!")
        
        # Show KM analysis
        st.subheader("Kilometer Analysis")
        st.write("Average KM per tire:", f"{display_tires['Current KM'].mean():,.0f} km")
        st.write("Highest KM tire:", f"{display_tires['Current KM'].max():,.0f} km")
        st.write("Lowest KM tire:", f"{display_tires['Current KM'].min():,.0f} km")
        
        # Show position map for selected tipper
        if selected_tipper != "All":
            st.subheader(f"Tire Position Map for {selected_tipper}")
            
            # Create a simple visual representation of tire positions
            position_map = """
            <style>
                .tire-map {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 10px;
                    margin: 20px 0;
                }
                .tire-position {
                    border: 1px solid #ddd;
                    padding: 10px;
                    text-align: center;
                    border-radius: 5px;
                }
                .front { grid-column: 2; }
            </style>
            
            <div class="tire-map">
                <div class="tire-position front">Front Left<br>{FL}</div>
                <div class="tire-position front">Front Right<br>{FR}</div>
                
                <div class="tire-position">Middle Left 1<br>{ML1}</div>
                <div class="tire-position">Middle Right 1<br>{MR1}</div>
                
                <div class="tire-position">Middle Left 2<br>{ML2}</div>
                <div class="tire-position">Middle Right 2<br>{MR2}</div>
                
                <div class="tire-position">Rear Left 1<br>{RL1}</div>
                <div class="tire-position">Rear Right 1<br>{RR1}</div>
                
                <div class="tire-position">Rear Left 2<br>{RL2}</div>
                <div class="tire-position">Rear Right 2<br>{RR2}</div>
            </div>
            """
            
            # Get tire numbers for each position
            position_data = {}
            for pos in [
                "Front Left", "Front Right",
                "Middle Left 1", "Middle Right 1",
                "Middle Left 2", "Middle Right 2",
                "Rear Left 1", "Rear Right 1",
                "Rear Left 2", "Rear Right 2"
            ]:
                tire = display_tires[display_tires['Position'] == pos]
                if not tire.empty:
                    tire_info = tire.iloc[0]
                    position_data[pos.replace(" ", "")] = (
                        f"{tire_info['Tire Number']}<br>"
                        f"{tire_info['Condition (%)']}%<br>"
                        f"{tire_info['Current KM']:,} km"
                    )
                else:
                    position_data[pos.replace(" ", "")] = "Empty"
            
            # Fill the position map with data
            filled_map = position_map.format(**position_data)
            st.markdown(filled_map, unsafe_allow_html=True)

elif menu == "Delete Tire":
    st.header("Delete Tire Record")
    
    if st.session_state.tires.empty:
        st.warning("No tires added yet!")
    else:
        # Select tipper first
        selected_tipper = st.selectbox(
            "Select Tipper",
            options=[f"Tipper-{i}" for i in range(1, 10)]
        )
        
        # Then select tire for that tipper
        tipper_tires = st.session_state.tires[
            st.session_state.tires['Tipper ID'] == selected_tipper
        ]
        
        if tipper_tires.empty:
            st.warning(f"No tires found for {selected_tipper}")
        else:
            tire_to_delete = st.selectbox(
                "Select tire to delete",
                options=tipper_tires['Tire Number'].unique()
            )
            
            if st.button("Delete Tire"):
                # Get image path before deletion
                image_path = st.session_state.tires[
                    (st.session_state.tires['Tipper ID'] == selected_tipper) & 
                    (st.session_state.tires['Tire Number'] == tire_to_delete)
                ]['Image Path'].values[0]
                
                # Delete the record
                st.session_state.tires = st.session_state.tires[
                    ~((st.session_state.tires['Tipper ID'] == selected_tipper) & 
                      (st.session_state.tires['Tire Number'] == tire_to_delete))
                ]
                
                # Delete the associated image
                if image_path and os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except:
                        st.warning("Could not delete tire image file")
                
                st.success(f"Tire {tire_to_delete} on {selected_tipper} deleted successfully!")

# Add some padding at the bottom
st.markdown("<br><br>", unsafe_allow_html=True)
