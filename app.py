import streamlit as st
from PIL import Image
import io
import pandas as pd
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        host="ep-cool-field-a4v58yfe-pooler.us-east-1.aws.neon.tech",
        database="neondb",
        user="neondb_owner",
        password="npg_3vkINAuWoQz6",
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
        condition_percent INTEGER NOT NULL,
        date_installed DATE NOT NULL,
        starting_kmr INTEGER NOT NULL,
        current_kmr INTEGER NOT NULL,
        last_checked TIMESTAMP NOT NULL,
        tire_status VARCHAR(20) NOT NULL DEFAULT 'new',
        UNIQUE(tipper_id, tire_number)
    )
    """)
    
    # Create tire_images table for storing images
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tire_images (
        id SERIAL PRIMARY KEY,
        tipper_id VARCHAR(50) NOT NULL,
        tire_number VARCHAR(50) NOT NULL,
        position VARCHAR(50) NOT NULL,
        image_data BYTEA NOT NULL,
        upload_time TIMESTAMP NOT NULL,
        FOREIGN KEY (tipper_id, tire_number) REFERENCES tires (tipper_id, tire_number) ON DELETE CASCADE
    )
    """)
    
    # Create tippers table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tippers (
        tipper_id VARCHAR(50) PRIMARY KEY,
        registration VARCHAR(100) NOT NULL
    )
    """)
    
    # Create inventory table for tire counts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tire_inventory (
        id SERIAL PRIMARY KEY,
        new_tires INTEGER DEFAULT 0,
        retread_tires INTEGER DEFAULT 0,
        scrap_tires INTEGER DEFAULT 0,
        last_updated TIMESTAMP NOT NULL
    )
    """)
    
    # Insert initial inventory if empty
    cursor.execute("SELECT COUNT(*) FROM tire_inventory")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO tire_inventory (new_tires, retread_tires, scrap_tires, last_updated)
        VALUES (20, 10, 5, %s)
        """, (datetime.now(),))
    
    # Insert tipper details if table is empty
    cursor.execute("SELECT COUNT(*) FROM tippers")
    if cursor.fetchone()[0] == 0:
        tipper_details = [
            ("TIPPER-1", "AP39UQ-0095"),
            ("TIPPER-2", "AP39UQ-0097"),
            ("TIPPER-3", "AP39UQ-0051"),
            ("TIPPER-4", "AP39UQ-0052"),
            ("TIPPER-5", "AP39UQ-0080"),
            ("TIPPER-6", "AP39UQ-0081"),
            ("TIPPER-7", "AP39UQ-0026"),
            ("TIPPER-8", "AP39UQ-0027"),
            ("TIPPER-9", "AP39UQ-0028")
        ]
        
        for tipper in tipper_details:
            cursor.execute(
                "INSERT INTO tippers (tipper_id, registration) VALUES (%s, %s)",
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
    cursor.execute("SELECT tipper_id, registration FROM tippers ORDER BY tipper_id")
    tippers = cursor.fetchall()
    cursor.close()
    conn.close()
    
    tipper_details = {}
    for tipper in tippers:
        display_name = f"{tipper[0]} - {tipper[1]}"
        tipper_details[tipper[0]] = display_name
    return tipper_details

# Function to get all tires for a specific tipper
def get_tires_for_tipper(tipper_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        tire_number, position, condition_percent, 
        date_installed, starting_kmr, current_kmr, last_checked, tire_status
    FROM tires
    WHERE tipper_id = %s
    ORDER BY position
    """, (tipper_id,))
    tires = cursor.fetchall()
    
    # Get images for each tire
    tires_with_images = []
    for tire in tires:
        cursor.execute("""
        SELECT image_data FROM tire_images
        WHERE tipper_id = %s AND tire_number = %s
        ORDER BY upload_time DESC
        """, (tipper_id, tire[0]))
        images = [row[0] for row in cursor.fetchall()]
        tires_with_images.append(tire + (images,))
    
    cursor.close()
    conn.close()
    
    return tires_with_images

# Function to save tire images to database
def save_tire_image(tipper_id, tire_number, position, image_file):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        INSERT INTO tire_images (
            tipper_id, tire_number, position, image_data, upload_time
        ) VALUES (%s, %s, %s, %s, %s)
        """, (
            tipper_id,
            tire_number,
            position,
            image_file.read(),
            datetime.now()
        ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Error saving image: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# Function to save/update tire data
def save_tire_data(tipper_id, tire_number, position, condition, date_installed, starting_kmr, current_kmr, tire_status):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if tire exists
        cursor.execute("""
        SELECT 1 FROM tires 
        WHERE tipper_id = %s AND tire_number = %s
        """, (tipper_id, tire_number))
        exists = cursor.fetchone() is not None
        
        if exists:
            # Update existing tire
            cursor.execute("""
            UPDATE tires SET
                position = %s,
                condition_percent = %s,
                date_installed = %s,
                starting_kmr = %s,
                current_kmr = %s,
                last_checked = %s,
                tire_status = %s
            WHERE tipper_id = %s AND tire_number = %s
            """, (
                position,
                condition,
                date_installed,
                starting_kmr,
                current_kmr,
                datetime.now(),
                tire_status,
                tipper_id,
                tire_number
            ))
        else:
            # Insert new tire
            cursor.execute("""
            INSERT INTO tires (
                tipper_id, tire_number, position,
                condition_percent, date_installed, starting_kmr,
                current_kmr, last_checked, tire_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                tipper_id,
                tire_number,
                position,
                condition,
                date_installed,
                starting_kmr,
                current_kmr,
                datetime.now(),
                tire_status
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

# Function to get tire inventory
def get_tire_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT new_tires, retread_tires, scrap_tires FROM tire_inventory ORDER BY id DESC LIMIT 1")
    inventory = cursor.fetchone()
    cursor.close()
    conn.close()
    return inventory

# Function to update tire inventory
def update_tire_inventory(new_tires, retread_tires, scrap_tires):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        INSERT INTO tire_inventory (new_tires, retread_tires, scrap_tires, last_updated)
        VALUES (%s, %s, %s, %s)
        """, (new_tires, retread_tires, scrap_tires, datetime.now()))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Error updating inventory: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# Function to get tire status color
def get_tire_color(condition):
    if condition >= 70:
        return 'green'
    elif condition >= 30:
        return 'orange'
    else:
        return 'red'

# Get tipper details
tipper_details = get_tipper_details()

# App title
st.title("🚛 Tipper Tire Management System")
st.markdown("---")

# Sidebar for navigation
menu = st.sidebar.selectbox(
    "Menu",
    ["Tire Management", "Tire Dashboard", "Tipper Info", "Inventory Management"]
)

if menu == "Tipper Info":
    st.header("ℹ️ Tipper Information")
    # Display all tippers in a clean table
    conn = get_db_connection()
    tipper_df = pd.read_sql("SELECT tipper_id as \"Tipper ID\", registration as Registration FROM tippers ORDER BY tipper_id", conn)
    conn.close()
    
    st.dataframe(
        tipper_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Add some statistics
    st.subheader("Tipper Statistics")
    conn = get_db_connection()
    stats_df = pd.read_sql("""
    SELECT 
        t.tipper_id as "Tipper ID",
        t.registration as Registration,
        COUNT(ty.tire_number) as "Tire Count",
        COALESCE(AVG(ty.condition_percent), 0) as "Avg Condition (%)",
        COALESCE(SUM(ty.current_kmr - ty.starting_kmr), 0) as "Total KMs Run"
    FROM tippers t
    LEFT JOIN tires ty ON t.tipper_id = ty.tipper_id
    GROUP BY t.tipper_id, t.registration
    ORDER BY t.tipper_id
    """, conn)
    conn.close()
    
    st.dataframe(
        stats_df.style.format({
            "Avg Condition (%)": "{:.1f}%",
            "Total KMs Run": "{:,.0f} km"
        }),
        use_container_width=True,
        hide_index=True
    )

elif menu == "Inventory Management":
    st.header("📦 Tire Inventory Management")
    
    # Get current inventory
    new_tires, retread_tires, scrap_tires = get_tire_inventory()
    
    with st.form("inventory_form"):
        st.subheader("Update Tire Inventory")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            new_tires_input = st.number_input("New Tires", min_value=0, value=new_tires)
        with col2:
            retread_tires_input = st.number_input("Retread Tires", min_value=0, value=retread_tires)
        with col3:
            scrap_tires_input = st.number_input("Scrap Tires", min_value=0, value=scrap_tires)
        
        if st.form_submit_button("Update Inventory"):
            if update_tire_inventory(new_tires_input, retread_tires_input, scrap_tires_input):
                st.success("Inventory updated successfully!")
            else:
                st.error("Failed to update inventory")
    
    # Display current inventory with cards
    st.subheader("Current Inventory Status")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("New Tires", new_tires)
    with col2:
        st.metric("Retread Tires", retread_tires)
    with col3:
        st.metric("Scrap Tires", scrap_tires)

elif menu == "Tire Management":
    st.header("🛠️ Tire Management")
    
    # Select tipper with proper display of all options
    selected_tipper = st.selectbox(
        "Select Tipper", 
        options=list(tipper_details.keys()),
        format_func=lambda x: tipper_details[x],
        index=0
    )
    
    # Define all tire positions
    positions = [
        "Front Left", "Front Right",
        "Middle Left 1", "Middle Right 1",
        "Middle Left 2", "Middle Right 2",
        "Rear Left 1", "Rear Right 1",
        "Rear Left 2", "Rear Right 2"
    ]
    
    # Get existing tires for this tipper
    existing_tires = get_tires_for_tipper(selected_tipper)
    
    # Create a form for all tires
    form = st.form(key="tire_management_form")
    with form:
        st.subheader(f"Tire Details for {tipper_details[selected_tipper]}")
        
        # Create two columns for better layout
        col1, col2 = st.columns(2)
        
        for i, position in enumerate(positions):
            # Alternate between columns
            col = col1 if i % 2 == 0 else col2
            
            with col:
                st.markdown(f"### {position}")
                
                # Find existing data for this position
                existing_data = next((tire for tire in existing_tires if tire[1] == position), None)
                
                # Tire number (fixed based on position)
                tire_number = f"Tire-{i+1}"
                st.text_input("Tire Number", value=tire_number, key=f"num_{position}", disabled=True)
                
                # Tire status
                tire_status = st.selectbox(
                    "Tire Status",
                    options=["new", "retread", "scrap"],
                    index=0 if not existing_data else ["new", "retread", "scrap"].index(existing_data[7]),
                    key=f"status_{position}"
                )
                
                # Image upload
                uploaded_file = st.file_uploader(
                    f"Upload {position} Tire Image",
                    type=["jpg", "jpeg", "png"],
                    key=f"img_{position}"
                )
                
                # Display existing images if available
                if existing_data and existing_data[8]:  # images are at index 8
                    st.write("Existing Images:")
                    img_cols = st.columns(3)
                    for idx, img_data in enumerate(existing_data[8]):
                        try:
                            with img_cols[idx % 3]:
                                image = Image.open(io.BytesIO(img_data))
                                st.image(image, caption=f"Image {idx+1}", width=150)
                        except:
                            st.warning(f"Could not load image {idx+1}")
                
                # Condition slider
                condition = st.slider(
                    "Condition (%)",
                    min_value=0, max_value=100,
                    value=existing_data[2] if existing_data else 80,
                    key=f"cond_{position}"
                )
                
                # Date installed
                date_installed = st.date_input(
                    "Date Installed",
                    value=existing_data[3] if existing_data else datetime.now().date(),
                    key=f"date_{position}"
                )
                
                # KMR inputs
                kmr_col1, kmr_col2 = st.columns(2)
                with kmr_col1:
                    starting_kmr = st.number_input(
                        "Starting KMR",
                        min_value=0,
                        value=existing_data[4] if existing_data else 0,
                        key=f"start_{position}"
                    )
                with kmr_col2:
                    current_kmr = st.number_input(
                        "Current KMR",
                        min_value=starting_kmr,
                        value=existing_data[5] if existing_data else starting_kmr,
                        key=f"current_{position}"
                    )
                
                st.markdown("---")
        
        # Submit button
        submitted = st.form_submit_button("Save All Tire Data")
    
    if submitted:
        progress_bar = st.progress(0)
        success_count = 0
        
        for i, position in enumerate(positions):
            tire_number = f"Tire-{i+1}"
            
            # Get other form data
            condition = st.session_state.get(f"cond_{position}")
            date_installed = st.session_state.get(f"date_{position}")
            starting_kmr = st.session_state.get(f"start_{position}")
            current_kmr = st.session_state.get(f"current_{position}")
            tire_status = st.session_state.get(f"status_{position}")
            
            # Save tire data to database
            if save_tire_data(
                selected_tipper, tire_number, position, 
                condition, date_installed, 
                starting_kmr, current_kmr, tire_status
            ):
                success_count += 1
            
            # Handle image upload separately
            uploaded_file = st.session_state.get(f"img_{position}")
            if uploaded_file is not None:
                if save_tire_image(selected_tipper, tire_number, position, uploaded_file):
                    success_count += 0.5  # partial success for image upload
            
            progress_bar.progress((i + 1) / len(positions))
        
        if success_count >= len(positions):
            st.success("All tire data saved successfully!")
        elif success_count > 0:
            st.warning(f"Saved data for {int(success_count)} out of {len(positions)} tires. Some updates may have failed.")
        else:
            st.error("Failed to save any tire data.")

elif menu == "Tire Dashboard":
    st.header("📊 Tire Dashboard")
    
    # Select tipper with proper display of all options
    selected_tipper = st.selectbox(
        "Select Tipper to View", 
        options=list(tipper_details.keys()),
        format_func=lambda x: tipper_details[x],
        index=0
    )
    
    # Get tire data
    tires = get_tires_for_tipper(selected_tipper)
    
    if not tires:
        st.warning(f"No tire data available for {tipper_details[selected_tipper]}")
    else:
        # Convert to DataFrame for visualization
        tires_df = pd.DataFrame(tires, columns=[
            'Tire Number', 'Position', 'Condition (%)',
            'Date Installed', 'Starting KMR', 'Current KMR', 
            'Last Checked', 'Tire Status', 'Images'
        ])
        
        # Calculate KMs Run
        tires_df['KMs Run'] = tires_df['Current KMR'] - tires_df['Starting KMR']
        
        # Show summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_condition = tires_df['Condition (%)'].mean()
            st.metric("Average Condition", f"{avg_condition:.1f}%")
        with col2:
            total_kms = tires_df['KMs Run'].sum()
            st.metric("Total KMs Run", f"{total_kms:,.0f} km")
        with col3:
            worst_tire = tires_df.loc[tires_df['Condition (%)'].idxmin()]
            st.metric("Worst Condition", 
                     f"{worst_tire['Condition (%)']}% ({worst_tire['Position']})",
                     delta=f"{worst_tire['KMs Run']:,.0f} km")
        with col4:
            new_tires = (tires_df['Tire Status'] == 'new').sum()
            st.metric("New Tires", new_tires)
        
        # Color coding for condition ranges
        st.markdown("""
        <style>
        .green { background-color: #d4edda; color: #155724; }
        .yellow { background-color: #fff3cd; color: #856404; }
        .red { background-color: #f8d7da; color: #721c24; }
        </style>
        """, unsafe_allow_html=True)
        
        # Condition legend
        st.markdown("""
        **Condition Colors:**  
        <span class="green">Good (70-100%)</span> | 
        <span class="yellow">Fair (30-69%)</span> | 
        <span class="red">Poor (0-29%)</span>
        """, unsafe_allow_html=True)
        
        # Detailed tire information with color coding
        st.subheader("Detailed Tire Information")
        
        # Apply color coding based on condition
        def color_tire_condition(val):
            color = get_tire_color(val)
            return f'background-color: {color}'
        
        detailed_df = tires_df[['Position', 'Tire Number', 'Starting KMR', 'Current KMR', 
                              'KMs Run', 'Condition (%)', 'Tire Status', 'Date Installed']]
        
        st.dataframe(
            detailed_df.style
            .applymap(color_tire_condition, subset=['Condition (%)'])
            .format({
                'Starting KMR': '{:,.0f}',
                'Current KMR': '{:,.0f}',
                'KMs Run': '{:,.0f}',
                'Condition (%)': '{:.0f}%'
            }),
            use_container_width=True,
            height=(len(tires_df) * 35) + 35
        )
        
        # Visual layout of all tires
        st.subheader("Tire Positions and Conditions")
        
        # Define the tire layout (simulating a truck view)
        positions_order = [
            ["Front Left", "Front Right"],
            ["Middle Left 1", "Middle Right 1"],
            ["Middle Left 2", "Middle Right 2"],
            ["Rear Left 1", "Rear Right 1"],
            ["Rear Left 2", "Rear Right 2"]
        ]
        
        # Create columns for the visual layout
        cols = st.columns([1, 2, 2, 1])
        
        for row_idx, row_positions in enumerate(positions_order):
            for col_idx, position in enumerate(row_positions):
                # Determine which column to use (centered layout)
                display_col = cols[col_idx + 1] if len(row_positions) == 2 else cols[1]
                
                with display_col:
                    tire_data = tires_df[tires_df['Position'] == position]
                    if not tire_data.empty:
                        tire_data = tire_data.iloc[0]
                        condition_color = get_tire_color(tire_data['Condition (%)'])
                        
                        # Display tire info in a container with color-coded border
                        with st.container():
                            st.markdown(
                                f"""<div style='border: 2px solid {condition_color}; border-radius: 5px; padding: 10px; margin-bottom: 10px;'>
                                <h4 style='color: {condition_color};'>{position} ({tire_data['Tire Number']})</h4>
                                <p><strong>Condition:</strong> <span style='color: {condition_color};'>{tire_data['Condition (%)']}%</span></p>
                                <p><strong>Status:</strong> {tire_data['Tire Status'].capitalize()}</p>
                                <p><strong>KMs Run:</strong> {tire_data['KMs Run']:,.0f} km</p>
                                <p><strong>Installed:</strong> {tire_data['Date Installed']}</p>
                                </div>""",
                                unsafe_allow_html=True
                            )
                            
                            # Display all images if available
                            if tire_data['Images'] and len(tire_data['Images']) > 0:
                                with st.expander("View Tire Images"):
                                    img_cols = st.columns(3)
                                    for idx, img_data in enumerate(tire_data['Images']):
                                        try:
                                            with img_cols[idx % 3]:
                                                image = Image.open(io.BytesIO(img_data))
                                                st.image(image, caption=f"Image {idx+1}", width=150)
                                        except:
                                            st.warning(f"Could not load image {idx+1}")
                    else:
                        with st.container():
                            st.markdown(
                                f"""<div style='border: 2px solid #cccccc; border-radius: 5px; padding: 10px; margin-bottom: 10px;'>
                                <h4>{position}</h4>
                                <p style='color: #666666;'>No data available</p>
                                </div>""",
                                unsafe_allow_html=True
                            )
        
        # Condition trend chart
        st.subheader("Condition Overview")
        st.bar_chart(tires_df.set_index('Position')['Condition (%)'])
        
        # Tires needing attention
        critical_tires = tires_df[tires_df['Condition (%)'] < 30]
        if not critical_tires.empty:
            st.warning("⚠️ The following tires need attention:")
            st.dataframe(
                critical_tires[['Position', 'Tire Number', 'Condition (%)', 'KMs Run', 'Tire Status']]
                .style.applymap(lambda x: 'color: red', subset=['Condition (%)'])
            )

# Run the app
if __name__ == "__main__":
    st.set_page_config(layout="wide")
