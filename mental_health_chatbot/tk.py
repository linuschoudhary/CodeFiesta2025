import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
from datetime import datetime, timedelta
import WordPreprocessing as wp
import sentimant_analysis as sa
import gemini as gemi
import consultants
from PIL import Image, ImageTk
import threading

# Database functions (same as original)
DB_NAME = 'saathi_chat_history.db'

def init_db():
    """Initializes the SQLite database and creates the chat table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_message(role, content):
    """Saves a single chat message to the database."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chats (date, time, role, content)
        VALUES (?, ?, ?, ?)
    ''', (date_str, time_str, role, content))
    conn.commit()
    conn.close()

def load_today_messages():
    """Loads all chat messages for the current day."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT time, role, content FROM chats WHERE date = ? ORDER BY id
    ''', (date_str,))
    
    messages = []
    for time_str, role, content in cursor.fetchall():
        messages.append({
            "role": role, 
            "content": content, 
            "time": time_str
        })
        
    conn.close()
    return messages

def load_messages_by_date(selected_date):
    """Loads chat messages for a specific date."""
    date_str = selected_date.strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT time, role, content FROM chats WHERE date = ? ORDER BY id
    ''', (date_str,))
    
    messages = []
    for time_str, role, content in cursor.fetchall():
        messages.append({
            "role": role, 
            "content": content, 
            "time": time_str
        })
        
    conn.close()
    return messages

def get_available_dates():
    """Get all dates that have chat history."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT date FROM chats ORDER BY date DESC
    ''')
    
    dates = [datetime.strptime(row[0], "%Y-%m-%d") for row in cursor.fetchall()]
    conn.close()
    return dates

def clear_today_chat_history():
    """Clears today's chat history from the database."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM chats WHERE date = ?
    ''', (date_str,))
    conn.commit()
    conn.close()

def check_distress_and_alert(distress_score, chat_history):
    """Check distress level and alert consultant if above threshold"""
    if distress_score >= 25:  # Threshold for consultant alert
        consultant = consultants.get_available_consultant()
        if consultant:
            consultant_id, name, email, phone, specialization, experience, availability = consultant
            
            # Send alert (in real implementation, this would send email)
            alert_sent = consultants.send_alert_to_consultant(
                email, name, chat_history, distress_score
            )
            
            # Log the alert
            consultants.log_consultant_alert(
                chat_history, distress_score, consultant_id, name
            )
            
            return {
                'alert_sent': alert_sent,
                'consultant_name': name,
                'consultant_email': email,
                'consultant_phone': phone,
                'specialization': specialization,
                'distress_score': distress_score
            }
    return None

class SAATHIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SAATHI: Mental Health Chat Bot")
        self.root.geometry("1200x800")
        self.root.configure(bg='#0E1117')
        
        # Initialize database
        init_db()
        
        # Session state
        self.chat_history = load_today_messages()
        self.last_analysis = {}
        self.consultant_alert = None
        self.current_page = "Chat"
        
        # Configure styles
        self.setup_styles()
        
        # Create main layout
        self.create_main_layout()
        
        # Show initial page
        self.show_chat_page()
    
    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        
        # Configure colors
        self.colors = {
            'bg': '#0E1117',
            'sidebar_bg': '#262730',
            'card_bg': '#262730',
            'text_primary': '#FFFFFF',
            'text_secondary': '#FAFAFA',
            'accent': '#FF4B4B',
            'success': '#00D4AA',
            'warning': '#FFA726',
            'danger': '#FF4B4B'
        }
        
        # Configure styles
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('Sidebar.TFrame', background=self.colors['sidebar_bg'])
        style.configure('Card.TFrame', background=self.colors['card_bg'], relief='raised', borderwidth=1)
        
        style.configure('Title.TLabel', background=self.colors['bg'], foreground=self.colors['text_primary'], font=('Arial', 16, 'bold'))
        style.configure('Subtitle.TLabel', background=self.colors['bg'], foreground=self.colors['text_primary'], font=('Arial', 12))
        style.configure('Normal.TLabel', background=self.colors['bg'], foreground=self.colors['text_primary'], font=('Arial', 10))
        style.configure('Sidebar.TLabel', background=self.colors['sidebar_bg'], foreground=self.colors['text_primary'], font=('Arial', 10))
        
        style.configure('Primary.TButton', background='#FF4B4B', foreground='white', font=('Arial', 10, 'bold'))
        style.configure('Secondary.TButton', background='#555555', foreground='white', font=('Arial', 10))
        
        style.configure('TEntry', fieldbackground='#262730', foreground='white')
        style.configure('TCombobox', fieldbackground='#262730', foreground='white')
        
    def create_main_layout(self):
        """Create the main application layout"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Sidebar
        self.sidebar_frame = ttk.Frame(main_container, width=250, style='Sidebar.TFrame')
        self.sidebar_frame.pack(side='left', fill='y', padx=(0, 10))
        self.sidebar_frame.pack_propagate(False)
        
        # Content area
        self.content_frame = ttk.Frame(main_container)
        self.content_frame.pack(side='right', fill='both', expand=True)
        
        # Setup sidebar
        self.setup_sidebar()
    
    def setup_sidebar(self):
        """Setup sidebar navigation and widgets"""
        # Title
        title_label = ttk.Label(self.sidebar_frame, text="SAATHI Navigation", style='Title.TLabel')
        title_label.pack(pady=20)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.sidebar_frame, style='Sidebar.TFrame')
        nav_frame.pack(fill='x', padx=10)
        
        self.chat_btn = ttk.Button(nav_frame, text="💬 Chat", command=lambda: self.show_page("Chat"), style='Primary.TButton')
        self.chat_btn.pack(fill='x', pady=5)
        
        self.consultants_btn = ttk.Button(nav_frame, text="👨‍⚕️ Consultants", command=lambda: self.show_page("Consultants"), style='Secondary.TButton')
        self.consultants_btn.pack(fill='x', pady=5)
        
        self.crisis_btn = ttk.Button(nav_frame, text="🚨 Crisis Help", command=lambda: self.show_page("Crisis Help"), style='Secondary.TButton')
        self.crisis_btn.pack(fill='x', pady=5)
        
        # Separator
        separator = ttk.Separator(self.sidebar_frame, orient='horizontal')
        separator.pack(fill='x', pady=20)
        
        # Sentiment Analysis Section
        analysis_title = ttk.Label(self.sidebar_frame, text="Sentiment Analysis Data", style='Sidebar.TLabel')
        analysis_title.pack(pady=10)
        
        # Messages count
        self.messages_count_label = ttk.Label(self.sidebar_frame, text=f"Today's messages: {len(self.chat_history)}", style='Sidebar.TLabel')
        self.messages_count_label.pack(pady=5)
        
        # Clear chat button
        clear_btn = ttk.Button(self.sidebar_frame, text="🗑️ Clear Today's Chat", command=self.clear_chat_callback, style='Secondary.TButton')
        clear_btn.pack(fill='x', padx=10, pady=10)
        
        # Date selection
        date_label = ttk.Label(self.sidebar_frame, text="📅 View Chats by Date", style='Sidebar.TLabel')
        date_label.pack(pady=10)
        
        self.date_var = tk.StringVar()
        self.date_combo = ttk.Combobox(self.sidebar_frame, textvariable=self.date_var, state='readonly')
        self.date_combo.pack(fill='x', padx=10, pady=5)
        self.date_combo.bind('<<ComboboxSelected>>', self.on_date_selected)
        
        # Update date options
        self.update_date_options()
        
        # Recent messages frame
        recent_label = ttk.Label(self.sidebar_frame, text="💬 Recent Messages", style='Sidebar.TLabel')
        recent_label.pack(pady=10)
        
        self.recent_messages_frame = ttk.Frame(self.sidebar_frame, style='Card.TFrame', height=120)
        self.recent_messages_frame.pack(fill='x', padx=10, pady=5)
        self.recent_messages_frame.pack_propagate(False)
        
        # Analysis results frame
        self.analysis_frame = ttk.Frame(self.sidebar_frame, style='Sidebar.TFrame')
        self.analysis_frame.pack(fill='x', padx=10, pady=10)
        
        # Update sidebar content
        self.update_sidebar_content()
    
    def update_date_options(self):
        """Update date combobox options"""
        available_dates = get_available_dates()
        date_options = ["Today"] + [date.strftime("%Y-%m-%d (%A)") for date in available_dates]
        self.date_combo['values'] = date_options
        if date_options:
            self.date_combo.set("Today")
    
    def on_date_selected(self, event):
        """Handle date selection change"""
        self.update_sidebar_content()
    
    def update_sidebar_content(self):
        """Update sidebar content based on selected date"""
        # Update recent messages
        for widget in self.recent_messages_frame.winfo_children():
            widget.destroy()
        
        selected_date_option = self.date_var.get()
        if not selected_date_option:
            selected_date_option = "Today"
        
        if selected_date_option == "Today":
            display_messages = self.chat_history
        else:
            selected_date_str = selected_date_option.split(" ")[0]
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d")
            display_messages = load_messages_by_date(selected_date)
        
        # Display recent messages (last 5)
        recent_text = tk.Text(self.recent_messages_frame, wrap='word', height=6, bg='#262626', fg='white', 
                             font=('Arial', 9), relief='flat', borderwidth=0)
        recent_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        if display_messages:
            for msg in display_messages[-5:]:
                content = msg["content"]
                if len(content) > 60:
                    content = content[:57] + "..."
                recent_text.insert('end', f"{msg['role']}: {content}\n\n")
        else:
            recent_text.insert('end', "No messages found\n")
        
        recent_text.config(state='disabled')
        
        # Update analysis frame
        for widget in self.analysis_frame.winfo_children():
            widget.destroy()
        
        if self.last_analysis:
            distress_score = self.last_analysis["distress_score"]
            
            # Crisis escalation logic
            crisis_label = ttk.Label(self.analysis_frame, text="Crisis Escalation Logic", style='Sidebar.TLabel')
            crisis_label.pack(pady=5)
            
            if distress_score >= 30:
                status_text = "🚨 CRITICAL: Consultant notified immediately"
                status_color = self.colors['danger']
            elif distress_score >= 25:
                status_text = "⚠️ MODERATE: Consultant alert activated"
                status_color = self.colors['warning']
            elif distress_score >= 15:
                status_text = "⚠️ MILD: Monitoring closely"
                status_color = self.colors['warning']
            else:
                status_text = f"✅ Normal range [Score: {distress_score}]"
                status_color = self.colors['success']
            
            status_label = ttk.Label(self.analysis_frame, text=status_text, foreground=status_color, style='Sidebar.TLabel')
            status_label.pack(pady=5)
            
            # Metrics
            metrics_frame = ttk.Frame(self.analysis_frame, style='Sidebar.TFrame')
            metrics_frame.pack(fill='x', pady=10)
            
            ttk.Label(metrics_frame, text=f"Distress Score: {distress_score}", style='Sidebar.TLabel').pack(anchor='w')
            ttk.Label(metrics_frame, text=f"Compound Score: {self.last_analysis['compound_score']:.2f}", style='Sidebar.TLabel').pack(anchor='w')
            ttk.Label(metrics_frame, text=f"Vader Label: {self.last_analysis['vader_label']}", style='Sidebar.TLabel').pack(anchor='w')
            ttk.Label(metrics_frame, text=f"Positive Score: {self.last_analysis['pos_score']:.2f}", style='Sidebar.TLabel').pack(anchor='w')
            ttk.Label(metrics_frame, text=f"Negative Score: {self.last_analysis['neg_score']:.2f}", style='Sidebar.TLabel').pack(anchor='w')
    
    def show_page(self, page_name):
        """Show the specified page"""
        self.current_page = page_name
        
        # Update button styles
        for btn in [self.chat_btn, self.consultants_btn, self.crisis_btn]:
            btn.configure(style='Secondary.TButton')
        
        if page_name == "Chat":
            self.chat_btn.configure(style='Primary.TButton')
            self.show_chat_page()
        elif page_name == "Consultants":
            self.consultants_btn.configure(style='Primary.TButton')
            self.show_consultants_page()
        elif page_name == "Crisis Help":
            self.crisis_btn.configure(style='Primary.TButton')
            self.show_crisis_help_page()
    
    def clear_content_frame(self):
        """Clear the content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_chat_page(self):
        """Show the chat page"""
        self.clear_content_frame()
        
        # Title
        title_label = ttk.Label(self.content_frame, text="SAATHI: Mental Health Chat Bot", style='Title.TLabel')
        title_label.pack(pady=10)
        
        subtitle_label = ttk.Label(self.content_frame, text="Your Wellness Assistant", style='Subtitle.TLabel')
        subtitle_label.pack(pady=5)
        
        # Consultant alert
        if self.consultant_alert:
            alert_frame = ttk.Frame(self.content_frame, style='Card.TFrame')
            alert_frame.pack(fill='x', padx=10, pady=10)
            
            alert_text = f"""🚨 CONSULTANT ALERT ACTIVATED

Consultant Assigned: {self.consultant_alert['consultant_name']}
Specialization: {self.consultant_alert['specialization']}
Contact: {self.consultant_alert['consultant_email']} | {self.consultant_alert['consultant_phone']}
Distress Level: {self.consultant_alert['distress_score']}/100

A professional will reach out to you shortly. Please continue sharing how you feel."""
            
            alert_label = ttk.Label(alert_frame, text=alert_text, foreground=self.colors['danger'], style='Normal.TLabel', justify='left')
            alert_label.pack(padx=10, pady=10)
        
        # Chat history container
        chat_container_frame = ttk.Frame(self.content_frame, style='Card.TFrame')
        chat_container_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Chat history title
        history_title = ttk.Label(chat_container_frame, text="Conversation History", style='Subtitle.TLabel')
        history_title.pack(anchor='w', padx=10, pady=10)
        
        # Chat display area
        self.chat_display = scrolledtext.ScrolledText(chat_container_frame, wrap='word', bg='#262730', fg='white', 
                                                     font=('Arial', 10), relief='flat', borderwidth=0)
        self.chat_display.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Input area
        input_frame = ttk.Frame(self.content_frame)
        input_frame.pack(fill='x', padx=10, pady=10)
        
        self.chat_input = tk.Text(input_frame, height=3, wrap='word', bg='#262730', fg='white', font=('Arial', 10))
        self.chat_input.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.chat_input.bind('<Return>', self.on_enter_pressed)
        
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side='right')
        
        send_btn = ttk.Button(button_frame, text="💬 Send", command=self.process_message, style='Primary.TButton')
        send_btn.pack(pady=5)
        
        clear_btn = ttk.Button(button_frame, text="🗑️ Clear", command=self.clear_chat_callback, style='Secondary.TButton')
        clear_btn.pack(pady=5)
        
        # Update chat display
        self.update_chat_display()
    
    def on_enter_pressed(self, event):
        """Handle Enter key press in chat input"""
        if event.state & 0x1:  # Shift+Enter for new line
            return
        else:
            self.process_message()
            return 'break'  # Prevent default behavior
    
    def process_message(self):
        """Process user message"""
        user_input = self.chat_input.get('1.0', 'end-1c').strip()
        
        if user_input:
            # Clear input
            self.chat_input.delete('1.0', 'end')
            
            # Process in a separate thread to prevent GUI freezing
            threading.Thread(target=self._process_message_thread, args=(user_input,), daemon=True).start()
    
    def _process_message_thread(self, user_input):
        """Thread function for processing messages"""
        # Save user message
        timestamp = datetime.now().strftime("%H:%M:%S")
        save_message("User", user_input)
        
        # Update chat history and display
        self.root.after(0, self._add_message_to_display, "User", user_input, timestamp)
        
        # Analysis logic
        chat = wp.Word_Preprocessing(user_input)
        distress_score, compound_score, vader_label, pos_score, neg_score, negative_sentiment_count = sa.analyse(chat)
        
        # Store analysis
        self.last_analysis = {
            "distress_score": distress_score,
            "compound_score": compound_score,
            "vader_label": vader_label,
            "pos_score": pos_score,
            "neg_score": neg_score,
            "negative_sentiment_count": negative_sentiment_count
        }
        
        # Check for distress and alert consultant
        consultant_alert = check_distress_and_alert(distress_score, self.chat_history)
        if consultant_alert:
            self.consultant_alert = consultant_alert
        
        # Gemini response
        gemini_chat_response = gemi.run_gemini_chat(user_input)
        
        # Save and display analysis message
        analysis_message = f"Sentiment Processed: {vader_label} (Score: {compound_score:.2f})"
        save_message("Saarthi (Analysis)", analysis_message)
        self.root.after(0, self._add_message_to_display, "Saarthi (Analysis)", analysis_message, datetime.now().strftime("%H:%M:%S"))
        
        # Save and display Gemini response
        save_message("Saarthi (Talk)", gemini_chat_response)
        self.root.after(0, self._add_message_to_display, "Saarthi (Talk)", gemini_chat_response, datetime.now().strftime("%H:%M:%S"))
        
        # Update sidebar
        self.root.after(0, self.update_sidebar_content)
        
        # Refresh chat page if consultant alert was triggered
        if consultant_alert:
            self.root.after(0, self.show_chat_page)
    
    def _add_message_to_display(self, role, content, timestamp):
        """Add a message to the chat display (thread-safe)"""
        # Add to chat history
        self.chat_history.append({
            "role": role, 
            "content": content, 
            "time": timestamp
        })
        
        # Update display
        self.update_chat_display()
        
        # Update messages count
        self.messages_count_label.config(text=f"Today's messages: {len(self.chat_history)}")
    
    def update_chat_display(self):
        """Update the chat display with current history"""
        self.chat_display.config(state='normal')
        self.chat_display.delete('1.0', 'end')
        
        if not self.chat_history:
            self.chat_display.insert('end', "Start the chat by typing a message below.\n")
        else:
            for message in self.chat_history:
                role_icon = "👤" if message["role"] == "User" else "🤖"
                self.chat_display.insert('end', f'[{message["time"]}] {role_icon} {message["role"]}:\n')
                self.chat_display.insert('end', f'{message["content"]}\n\n')
        
        self.chat_display.config(state='disabled')
        self.chat_display.see('end')
    
    def clear_chat_callback(self):
        """Clear chat history"""
        self.chat_history = []
        self.last_analysis = {}
        self.consultant_alert = None
        clear_today_chat_history()
        
        # Update displays
        if self.current_page == "Chat":
            self.update_chat_display()
        self.update_sidebar_content()
        self.messages_count_label.config(text=f"Today's messages: {len(self.chat_history)}")
    
    def show_consultants_page(self):
        """Show the consultants management page"""
        self.clear_content_frame()
        
        # Title
        title_label = ttk.Label(self.content_frame, text="👨‍⚕️ Consultant Management", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: View Consultants
        view_tab = ttk.Frame(notebook)
        notebook.add(view_tab, text="View Consultants")
        
        self.setup_view_consultants_tab(view_tab)
        
        # Tab 2: Add Consultant
        add_tab = ttk.Frame(notebook)
        notebook.add(add_tab, text="Add Consultant")
        
        self.setup_add_consultant_tab(add_tab)
        
        # Tab 3: Consultant Alerts
        alerts_tab = ttk.Frame(notebook)
        notebook.add(alerts_tab, text="Consultant Alerts")
        
        self.setup_consultant_alerts_tab(alerts_tab)
    
    def setup_view_consultants_tab(self, parent):
        """Setup the view consultants tab"""
        consultants_list = consultants.get_all_consultants()
        
        if not consultants_list:
            no_consultants_label = ttk.Label(parent, text="No consultants available", style='Normal.TLabel')
            no_consultants_label.pack(pady=20)
            return
        
        # Create a canvas and scrollbar for the consultants list
        canvas = tk.Canvas(parent, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Card.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Add consultants to scrollable frame
        for i, consultant in enumerate(consultants_list):
            id, name, email, phone, specialization, exp, availability = consultant
            
            consultant_frame = ttk.Frame(scrollable_frame, style='Card.TFrame')
            consultant_frame.pack(fill='x', padx=10, pady=5)
            
            # Header with expand/collapse
            header_frame = ttk.Frame(consultant_frame, style='Card.TFrame')
            header_frame.pack(fill='x', padx=10, pady=10)
            
            name_label = ttk.Label(header_frame, text=f"👤 {name} - {specialization}", style='Subtitle.TLabel')
            name_label.pack(side='left')
            
            # Details frame (initially hidden)
            details_frame = ttk.Frame(consultant_frame, style='Card.TFrame')
            
            def toggle_details(frame=details_frame, btn=None):
                if frame.winfo_ismapped():
                    frame.pack_forget()
                else:
                    frame.pack(fill='x', padx=10, pady=10)
            
            # Toggle button
            toggle_btn = ttk.Button(header_frame, text="▼ Details", command=toggle_details, style='Secondary.TButton')
            toggle_btn.pack(side='right')
            
            # Details content
            col1 = ttk.Frame(details_frame, style='Card.TFrame')
            col1.pack(side='left', fill='x', expand=True, padx=(0, 10))
            
            col2 = ttk.Frame(details_frame, style='Card.TFrame')
            col2.pack(side='right', fill='x', expand=True)
            
            ttk.Label(col1, text=f"Email: {email}", style='Normal.TLabel').pack(anchor='w')
            ttk.Label(col1, text=f"Phone: {phone}", style='Normal.TLabel').pack(anchor='w')
            ttk.Label(col1, text=f"Experience: {exp} years", style='Normal.TLabel').pack(anchor='w')
            
            ttk.Label(col2, text=f"Specialization: {specialization}", style='Normal.TLabel').pack(anchor='w')
            ttk.Label(col2, text=f"Availability: {availability}", style='Normal.TLabel').pack(anchor='w')
            
            # Action buttons
            action_frame = ttk.Frame(details_frame, style='Card.TFrame')
            action_frame.pack(fill='x', pady=10)
            
            contact_btn = ttk.Button(action_frame, text=f"Contact {name.split()[0]}", 
                                   command=lambda n=name, p=phone, e=email: self.contact_consultant(n, p, e),
                                   style='Secondary.TButton')
            contact_btn.pack(side='left', padx=(0, 10))
            
            deactivate_btn = ttk.Button(action_frame, text="Deactivate", 
                                      command=lambda cid=id, n=name: self.deactivate_consultant(cid, n),
                                      style='Secondary.TButton')
            deactivate_btn.pack(side='left')
    
    def contact_consultant(self, name, phone, email):
        """Contact consultant action"""
        messagebox.showinfo(f"Contact {name}", f"Would contact {name} at {phone} or {email}")
    
    def deactivate_consultant(self, consultant_id, name):
        """Deactivate consultant"""
        if messagebox.askyesno("Confirm Deactivation", f"Are you sure you want to deactivate {name}?"):
            consultants.deactivate_consultant(consultant_id)
            messagebox.showinfo("Success", f"Consultant {name} deactivated")
            # Refresh the consultants page
            self.show_consultants_page()
    
    def setup_add_consultant_tab(self, parent):
        """Setup the add consultant tab"""
        form_frame = ttk.Frame(parent, style='Card.TFrame')
        form_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        ttk.Label(form_frame, text="Add New Consultant", style='Subtitle.TLabel').pack(pady=10)
        
        # Form fields
        fields_frame = ttk.Frame(form_frame, style='Card.TFrame')
        fields_frame.pack(fill='x', pady=10)
        
        # Name
        ttk.Label(fields_frame, text="Full Name *", style='Normal.TLabel').grid(row=0, column=0, sticky='w', pady=5)
        name_entry = ttk.Entry(fields_frame, width=30)
        name_entry.grid(row=0, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Email
        ttk.Label(fields_frame, text="Email *", style='Normal.TLabel').grid(row=1, column=0, sticky='w', pady=5)
        email_entry = ttk.Entry(fields_frame, width=30)
        email_entry.grid(row=1, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Phone
        ttk.Label(fields_frame, text="Phone *", style='Normal.TLabel').grid(row=2, column=0, sticky='w', pady=5)
        phone_entry = ttk.Entry(fields_frame, width=30)
        phone_entry.grid(row=2, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Specialization
        ttk.Label(fields_frame, text="Specialization *", style='Normal.TLabel').grid(row=3, column=0, sticky='w', pady=5)
        specialization_entry = ttk.Entry(fields_frame, width=30)
        specialization_entry.grid(row=3, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Experience
        ttk.Label(fields_frame, text="Years of Experience", style='Normal.TLabel').grid(row=4, column=0, sticky='w', pady=5)
        experience_spinbox = tk.Spinbox(fields_frame, from_=0, to=50, width=28)
        experience_spinbox.grid(row=4, column=1, sticky='ew', pady=5, padx=(10, 0))
        experience_spinbox.delete(0, 'end')
        experience_spinbox.insert(0, '5')
        
        # Availability
        ttk.Label(fields_frame, text="Availability", style='Normal.TLabel').grid(row=5, column=0, sticky='w', pady=5)
        availability_entry = ttk.Entry(fields_frame, width=30)
        availability_entry.grid(row=5, column=1, sticky='ew', pady=5, padx=(10, 0))
        availability_entry.insert(0, '9 AM - 6 PM')
        
        # Configure grid weights
        fields_frame.columnconfigure(1, weight=1)
        
        def add_consultant():
            name = name_entry.get().strip()
            email = email_entry.get().strip()
            phone = phone_entry.get().strip()
            specialization = specialization_entry.get().strip()
            experience = int(experience_spinbox.get())
            availability = availability_entry.get().strip()
            
            if not all([name, email, phone, specialization]):
                messagebox.showerror("Error", "Please fill all required fields")
                return
            
            consultants.add_consultant(name, email, phone, specialization, experience, availability)
            messagebox.showinfo("Success", f"Consultant {name} added successfully!")
            
            # Clear form
            for entry in [name_entry, email_entry, phone_entry, specialization_entry]:
                entry.delete(0, 'end')
            experience_spinbox.delete(0, 'end')
            experience_spinbox.insert(0, '5')
            availability_entry.delete(0, 'end')
            availability_entry.insert(0, '9 AM - 6 PM')
        
        add_btn = ttk.Button(form_frame, text="Add Consultant", command=add_consultant, style='Primary.TButton')
        add_btn.pack(pady=20)
    
    def setup_consultant_alerts_tab(self, parent):
        """Setup the consultant alerts tab"""
        alert_frame = ttk.Frame(parent, style='Card.TFrame')
        alert_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        ttk.Label(alert_frame, text="Recent Consultant Alerts", style='Subtitle.TLabel').pack(pady=10)
        ttk.Label(alert_frame, text="Alert history would be displayed here", style='Normal.TLabel').pack(pady=20)
    
    def show_crisis_help_page(self):
        """Show the crisis help page"""
        self.clear_content_frame()
        
        # Title
        title_label = ttk.Label(self.content_frame, text="🚨 Crisis Help & Resources", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Emergency alert
        alert_frame = ttk.Frame(self.content_frame, style='Card.TFrame')
        alert_frame.pack(fill='x', padx=10, pady=10)
        
        alert_text = """IMMEDIATE HELP AVAILABLE

If you're in crisis or having thoughts of self-harm, please contact:"""
        
        alert_label = ttk.Label(alert_frame, text=alert_text, foreground=self.colors['danger'], style='Normal.TLabel', justify='left')
        alert_label.pack(padx=10, pady=10)
        
        # Two column layout
        columns_frame = ttk.Frame(self.content_frame)
        columns_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left column - Emergency Contacts
        left_frame = ttk.Frame(columns_frame, style='Card.TFrame')
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        ttk.Label(left_frame, text="Emergency Contacts", style='Subtitle.TLabel').pack(pady=10)
        
        contacts_text = """National Suicide Prevention Lifeline
📞 1-800-273-8255
🌐 suicidepreventionlifeline.org

Crisis Text Line
💬 Text HOME to 741741

Emergency Services
🚑 Dial 911"""
        
        contacts_label = ttk.Label(left_frame, text=contacts_text, style='Normal.TLabel', justify='left')
        contacts_label.pack(padx=10, pady=10)
        
        # Right column - Online Resources
        right_frame = ttk.Frame(columns_frame, style='Card.TFrame')
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        ttk.Label(right_frame, text="Online Resources", style='Subtitle.TLabel').pack(pady=10)
        
        resources_text = """Mental Health America
🌐 mhanational.org

National Alliance on Mental Illness
🌐 nami.org

Crisis Chat
🌐 crisischat.org"""
        
        resources_label = ttk.Label(right_frame, text=resources_text, style='Normal.TLabel', justify='left')
        resources_label.pack(padx=10, pady=10)
        
        # Bottom message
        bottom_frame = ttk.Frame(self.content_frame, style='Card.TFrame')
        bottom_frame.pack(fill='x', padx=10, pady=10)
        
        reminder_text = """Remember: You're not alone. Professional help is available and effective. 
Your mental health matters."""
        
        reminder_label = ttk.Label(bottom_frame, text=reminder_text, style='Normal.TLabel', justify='left')
        reminder_label.pack(padx=10, pady=10)

def main():
    """Main function to run the SAATHI application"""
    root = tk.Tk()
    app = SAATHIApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()