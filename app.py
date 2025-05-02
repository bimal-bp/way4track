import streamlit as st
from PIL import Image
import os
import pandas as pd
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        host="ep-bitter-snowflake-a4vh53sb-pooler.us-east-1.aws.neon.tech",
        database="neondb",
        user="neondb_owner",
        password="npg_AyD21VBQvTPW",
        sslmode="require"
    )

# Initialize database tables
def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tires table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tires (
        id SERIAL PRIMARY KEY,
        tipper_id VARCHAR(50) NOT NULL,
        tire_number VARCHAR(50) NOT NULL,
        position VARCHAR(50) NOT NULL,
        image_paths TEXT[],
        condition_percent INTEGER NOT NULL,
        date_installed DATE NOT NULL,
        starting_kmr INTEGER NOT NULL,
        current_kmr INTEGER NOT NULL,
        last_checked TIMESTAMP NOT NULL,
        UNIQUE(tipper_id, tire_number)
    )
    """)
    
    # Create tippers table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tippers (
        tipper_id VARCHAR(50) PRIMARY KEY,
        registration VARCHAR(100) NOT NULL,
        description VARCHAR(100)
    )
    """)
    
    # Insert tipper details if table is empty
    cursor.execute("SELECT COUNT(*) FROM tippers")
    if cursor.fetchone()[0] == 0:
        tipper_details = [
            ("TIPPER-1", "JHOSB4166", "WATER TANKER"),
            ("TIPPER-2", "AP39UQ-0095", None),
            ("TIPPER-3", "AP39UQ-0097", "ROC"),
            ("TIPPER-4", "AP39UW-9880", "ROCK BODY"),
            ("TIPPER-5", "AP39UW-9881", "ROCK BODY"),
            ("TIPPER-6", "AP39UY-4651", "ROCK BODY"),
            ("TIPPER-7", "AP39UY-4652", "ROCK BODY"),
            ("TIPPER-8", "AP39WC-0926", "ROCK BODY"),
            ("TIPPER-9", "AP39WC-0927", "ROCK BODY")
        ]
        
        for tipper in tipper_details:
            cursor.execute(
                "INSERT INTO tippers (tipper_id, registration, description) VALUES (%s, %s, %s)",
                tipper
            )
    
    conn.commit()
    cursor.close()
    conn.close()

# Initialize database on app start
initialize_database()

# Function to get all tipper details
def get_tipper_details():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT tipper_id, registration, description FROM tippers")
    tippers = cursor.fetchall()
    cursor.close()
    conn.close()
    
    tipper_details = {}
    for tipper in tippers:
        display_name = f"{tipper[1]}"
        if tipper[2]:
            display_name += f" ({tipper[2]})"
        tipper_details[tipper[0]] = display_name
    return tipper_details

# Function to get all tires
def get_all_tires():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        tipper_id, tire_number, position, image_paths, 
        condition_percent, date_installed, starting_kmr, 
        current_kmr, last_checked
    FROM tires
    """)
    tires = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not tires:
        return pd.DataFrame(columns=[
            'Tipper ID', 'Tire Number', 'Position', 'Image Paths',
            'Condition (%)', 'Date Installed', 'Starting KMR',
            'Current KMR', 'Last Checked'
        ])
    
    return pd.DataFrame(tires, columns=[
        'Tipper ID', 'Tire Number', 'Position', 'Image Paths',
        'Condition (%)', 'Date Installed', 'Starting KMR',
        'Current KMR', 'Last Checked'
    ])

# Function to add/update tire
def save_tire(tire_data, is_update=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if is_update:
            cursor.execute("""
            UPDATE tires SET
                position = %s,
                image_paths = %s,
                condition_percent = %s,
                date_installed = %s,
                starting_kmr = %s,
                current_kmr = %s,
                last_checked = %s
            WHERE tipper_id = %s AND tire_number = %s
            """, (
                tire_data['position'],
                tire_data['image_paths'],
                tire_data['condition_percent'],
                tire_data['date_installed'],
                tire_data['starting_kmr'],
                tire_data['current_kmr'],
                tire_data['last_checked'],
                tire_data['tipper_id'],
                tire_data['tire_number']
            ))
        else:
            cursor.execute("""
            INSERT INTO tires (
                tipper_id, tire_number, position, image_paths,
                condition_percent, date_installed, starting_kmr,
                current_kmr, last_checked
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                tire_data['tipper_id'],
                tire_data['tire_number'],
                tire_data['position'],
                tire_data['image_paths'],
                tire_data['condition_percent'],
                tire_data['date_installed'],
                tire_data['starting_kmr'],
                tire_data['current_kmr'],
                tire_data['last_checked']
            ))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Database error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# Function to delete tire
def delete_tire(tipper_id, tire_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First get image paths to delete files
        cursor.execute(
            "SELECT image_paths FROM tires WHERE tipper_id = %s AND tire_number = %s",
            (tipper_id, tire_number)
        )
        result = cursor.fetchone()
        image_paths = result[0] if result else None
        
        # Delete the record
        cursor.execute(
            "DELETE FROM tires WHERE tipper_id = %s AND tire_number = %s",
            (tipper_id, tire_number)
        )
        conn.commit()
        
        # Delete associated images
        if image_paths:
            for img_path in image_paths:
                if img_path and os.path.exists(img_path):
                    try:
                        os.remove(img_path)
                    except:
                        st.warning(f"Could not delete tire image file: {img_path}")
        
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Database error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# Create directories if they don't exist
os.makedirs("tire_images", exist_ok=True)

# Get tipper details
tipper_details = get_tipper_details()

# App title
st.title("Tipper Tire Management System")
st.subheader("Track and manage tires across your fleet of tippers")

# Sidebar for navigation
menu = st.sidebar.selectbox(
    "Menu",
    ["Add/Update Tire", "View All Tires", "Tire Dashboard", "Delete Tire", "Tipper Info"]
)

if menu == "Tipper Info":
    st.header("Tipper Information")
    tipper_info_df = pd.DataFrame.from_dict(tipper_details, orient='index', columns=['Registration'])
    st.dataframe(tipper_info_df)

elif menu == "Add/Update Tire":
    st.header("Add or Update Tire Information")
    
    # Form for tire details
    with st.form("tire_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            tipper_id = st.selectbox(
                "Tipper ID", 
                options=list(tipper_details.keys()),
                format_func=lambda x: f"{x} - {tipper_details[x]}",
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
            starting_kmr = st.number_input("Starting KMR When Installed", min_value=0, step=1000)
            current_kmr = st.number_input("Current KMR", min_value=starting_kmr, step=1000, value=starting_kmr)
            image_files = st.file_uploader("Upload Tire Images (Multiple allowed)", 
                                         type=["jpg", "png", "jpeg"], 
                                         accept_multiple_files=True)
        
        submitted = st.form_submit_button("Save Tire")
        
        if submitted:
            # Handle image uploads
            image_paths = []
            if image_files:
                for i, image_file in enumerate(image_files):
                    ext = image_file.name.split('.')[-1]
                    image_path = f"tire_images/{tipper_id}_{tire_number}_{i}.{ext}"
                    with open(image_path, "wb") as f:
                        f.write(image_file.getbuffer())
                    image_paths.append(image_path)
            
            # Check if this tire already exists
            tires_df = get_all_tires()
            existing_tire = tires_df[
                (tires_df['Tipper ID'] == tipper_id) & 
                (tires_df['Tire Number'] == tire_number)
            ]
            
            tire_data = {
                'tipper_id': tipper_id,
                'tire_number': tire_number,
                'position': position,
                'image_paths': image_paths,
                'condition_percent': condition,
                'date_installed': date_installed,
                'starting_kmr': starting_kmr,
                'current_kmr': current_kmr,
                'last_checked': datetime.now()
            }
            
            if not existing_tire.empty:
                # Update existing tire
                if save_tire(tire_data, is_update=True):
                    st.success(f"Tire {tire_number} on {tipper_id} updated successfully!")
            else:
                # Add new tire
                if save_tire(tire_data):
                    st.success(f"Tire {tire_number} added to {tipper_id} successfully!")
                    
elif menu == "View All Tires":
    st.header("All Tires Information")
    tires_df = get_all_tires()
    
    if tires_df.empty:
        st.warning("No tires added yet!")
    else:
        # Filter by tipper if desired
        selected_tipper = st.selectbox(
            "Filter by Tipper (or view all)",
            options=["All"] + list(tipper_details.keys()),
            format_func=lambda x: f"{x} - {tipper_details[x]}" if x != "All" else "All"
        )
        
        if selected_tipper != "All":
            display_tires = tires_df[tires_df['Tipper ID'] == selected_tipper]
        else:
            display_tires = tires_df
        
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
            tire_data = tires_df[
                (tires_df['Tipper ID'] == tipper_id) & 
                (tires_df['Tire Number'] == tire_num)
            ].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"Tipper: {tipper_id} - {tipper_details[tipper_id]}")
                st.subheader(f"Tire: {tire_num}")
                st.write(f"**Position:** {tire_data['Position']}")
                st.write(f"**Condition:** {tire_data['Condition (%)']}% remaining")
                st.write(f"**Date Installed:** {tire_data['Date Installed']}")
                st.write(f"**Starting KMR:** {tire_data['Starting KMR']:,} km")
                st.write(f"**Current KMR:** {tire_data['Current KMR']:,} km")
                st.write(f"**Total KMs Run:** {tire_data['Current KMR'] - tire_data['Starting KMR']:,} km")
                st.write(f"**Last Checked:** {tire_data['Last Checked']}")
                
            with col2:
                if tire_data['Image Paths'] and len(tire_data['Image Paths']) > 0:
                    st.subheader("Tire Images")
                    for img_path in tire_data['Image Paths']:
                        if img_path and os.path.exists(img_path):
                            try:
                                image = Image.open(img_path)
                                st.image(image, caption=f"{tipper_id} - {tire_num}", width=300)
                            except:
                                st.warning(f"Could not load image: {img_path}")
                        else:
                            st.warning(f"Image not found: {img_path}")
                else:
                    st.warning("No images available for this tire")

elif menu == "Tire Dashboard":
    st.header("Tire Condition Dashboard")
    tires_df = get_all_tires()
    
    if tires_df.empty:
        st.warning("No tires added yet!")
    else:
        # Filter by tipper if desired
        selected_tipper = st.selectbox(
            "View Dashboard for Tipper (or view all)",
            options=["All"] + list(tipper_details.keys()),
            format_func=lambda x: f"{x} - {tipper_details[x]}" if x != "All" else "All"
        )
        
        if selected_tipper != "All":
            display_tires = tires_df[tires_df['Tipper ID'] == selected_tipper]
        else:
            display_tires = tires_df
        
        # Display condition summary
        st.subheader("Condition Summary")
        st.bar_chart(display_tires.set_index(['Tipper ID', 'Tire Number'])['Condition (%)'])
        
        # Show tires that need attention (condition < 30%)
        critical_tires = display_tires[display_tires['Condition (%)'] < 30]
        if not critical_tires.empty:
            st.warning("The following tires need immediate attention:")
            st.dataframe(critical_tires[['Tipper ID', 'Tire Number', 'Position', 'Condition (%)', 'Current KMR']])
        else:
            st.success("All tires are in good condition!")
        
        # Show KM analysis
        st.subheader("Kilometer Analysis")
        display_tires['KMs Run'] = display_tires['Current KMR'] - display_tires['Starting KMR']
        st.write("Average KM run per tire:", f"{display_tires['KMs Run'].mean():,.0f} km")
        st.write("Highest KM run tire:", f"{display_tires['KMs Run'].max():,.0f} km")
        st.write("Lowest KM run tire:", f"{display_tires['KMs Run'].min():,.0f} km")
        
        # Show position map for selected tipper
        if selected_tipper != "All":
            st.subheader(f"Tire Position Map for {selected_tipper} - {tipper_details[selected_tipper]}")
            
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
                        f"{(tire_info['Current KMR'] - tire_info['Starting KMR']):,} km"
                    )
                else:
                    position_data[pos.replace(" ", "")] = "Empty"
            
            # Fill the position map with data
            filled_map = position_map.format(**position_data)
            st.markdown(filled_map, unsafe_allow_html=True)

elif menu == "Delete Tire":
    st.header("Delete Tire Record")
    tires_df = get_all_tires()
    
    if tires_df.empty:
        st.warning("No tires added yet!")
    else:
        # Select tipper first
        selected_tipper = st.selectbox(
            "Select Tipper",
            options=list(tipper_details.keys()),
            format_func=lambda x: f"{x} - {tipper_details[x]}"
        )
        
        # Then select tire for that tipper
        tipper_tires = tires_df[tires_df['Tipper ID'] == selected_tipper]
        
        if tipper_tires.empty:
            st.warning(f"No tires found for {selected_tipper}")
        else:
            tire_to_delete = st.selectbox(
                "Select tire to delete",
                options=tipper_tires['Tire Number'].unique()
            )
            
            if st.button("Delete Tire"):
                if delete_tire(selected_tipper, tire_to_delete):
                    st.success(f"Tire {tire_to_delete} on {selected_tipper} deleted successfully!")
                    # Refresh the tires dataframe
                    tires_df = get_all_tires()

# Add some padding at the bottom
st.markdown("<br><br>", unsafe_allow_html=True)
