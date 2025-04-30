import streamlit as st
from PIL import Image
import os
import pandas as pd

# Initialize session state for tire data
if 'tires' not in st.session_state:
    st.session_state.tires = pd.DataFrame(columns=[
        'Tire Number', 
        'Position', 
        'Image Path', 
        'Condition (%)', 
        'Last Checked'
    ])

# Create directories if they don't exist
os.makedirs("tire_images", exist_ok=True)

# App title
st.title("Tipper Tire Management System")
st.subheader("Track and manage your tipper's 10 tires")

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
            image_file = st.file_uploader("Upload Tire Image", type=["jpg", "png", "jpeg"])
        
        submitted = st.form_submit_button("Save Tire")
        
        if submitted:
            # Handle image upload
            image_path = None
            if image_file is not None:
                image_path = f"tire_images/{tire_number}.{image_file.name.split('.')[-1]}"
                with open(image_path, "wb") as f:
                    f.write(image_file.getbuffer())
            
            # Update or add tire data
            if tire_number in st.session_state.tires['Tire Number'].values:
                # Update existing tire
                idx = st.session_state.tires[st.session_state.tires['Tire Number'] == tire_number].index[0]
                st.session_state.tires.at[idx, 'Position'] = position
                st.session_state.tires.at[idx, 'Condition (%)'] = condition
                if image_path:
                    st.session_state.tires.at[idx, 'Image Path'] = image_path
                st.session_state.tires.at[idx, 'Last Checked'] = pd.Timestamp.now()
                st.success(f"Tire {tire_number} updated successfully!")
            else:
                # Add new tire
                new_tire = {
                    'Tire Number': tire_number,
                    'Position': position,
                    'Image Path': image_path,
                    'Condition (%)': condition,
                    'Last Checked': pd.Timestamp.now()
                }
                st.session_state.tires = st.session_state.tires.append(new_tire, ignore_index=True)
                st.success(f"Tire {tire_number} added successfully!")

elif menu == "View All Tires":
    st.header("All Tires Information")
    
    if st.session_state.tires.empty:
        st.warning("No tires added yet!")
    else:
        # Display all tires in a table
        st.dataframe(st.session_state.tires)
        
        # Show details for selected tire
        selected_tire = st.selectbox(
            "Select a tire to view details",
            options=st.session_state.tires['Tire Number'].unique()
        )
        
        tire_data = st.session_state.tires[st.session_state.tires['Tire Number'] == selected_tire].iloc[0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"Tire: {tire_data['Tire Number']}")
            st.write(f"**Position:** {tire_data['Position']}")
            st.write(f"**Condition:** {tire_data['Condition (%)']}% remaining")
            st.write(f"**Last Checked:** {tire_data['Last Checked']}")
            
        with col2:
            if tire_data['Image Path'] and os.path.exists(tire_data['Image Path']):
                try:
                    image = Image.open(tire_data['Image Path'])
                    st.image(image, caption=f"{selected_tire} Image", width=300)
                except:
                    st.warning("Could not load image")
            else:
                st.warning("No image available for this tire")

elif menu == "Tire Dashboard":
    st.header("Tire Condition Dashboard")
    
    if st.session_state.tires.empty:
        st.warning("No tires added yet!")
    else:
        # Display condition summary
        st.subheader("Condition Summary")
        st.bar_chart(st.session_state.tires.set_index('Tire Number')['Condition (%)'])
        
        # Show tires that need attention (condition < 30%)
        critical_tires = st.session_state.tires[st.session_state.tires['Condition (%)'] < 30]
        if not critical_tires.empty:
            st.warning("The following tires need immediate attention:")
            st.dataframe(critical_tires[['Tire Number', 'Position', 'Condition (%)']])
        else:
            st.success("All tires are in good condition!")
        
        # Show position map
        st.subheader("Tire Position Map")
        
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
            tire = st.session_state.tires[st.session_state.tires['Position'] == pos]
            if not tire.empty:
                position_data[pos.replace(" ", "")] = f"{tire.iloc[0]['Tire Number']} ({tire.iloc[0]['Condition (%)']}%)"
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
        tire_to_delete = st.selectbox(
            "Select tire to delete",
            options=st.session_state.tires['Tire Number'].unique()
        )
        
        if st.button("Delete Tire"):
            # Get image path before deletion
            image_path = st.session_state.tires[
                st.session_state.tires['Tire Number'] == tire_to_delete
            ]['Image Path'].values[0]
            
            # Delete the record
            st.session_state.tires = st.session_state.tires[
                st.session_state.tires['Tire Number'] != tire_to_delete
            ]
            
            # Delete the associated image
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except:
                    st.warning("Could not delete tire image file")
            
            st.success(f"Tire {tire_to_delete} deleted successfully!")

# Add some padding at the bottom
st.markdown("<br><br>", unsafe_allow_html=True)
