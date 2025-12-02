from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('TkAgg')  
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import threading
import sys
import os

class ParkUI:
    """
    Real-time visualization UI for the amusement park simulation.
    Displays rides, queues, facilities, and park capacity.
    Must be run on the main thread (macOS requirement).
    """
    def __init__(self, park, clock, metrics, rides, food_trucks, merch_stands, bathrooms):
        self.park = park
        self.clock = clock
        self.metrics = metrics
        self.rides = rides
        self.food_trucks = food_trucks
        self.merch_stands = merch_stands
        self.bathrooms = bathrooms
        self.running = False
        
        # Park configuration
        self.max_capacity = 1000  # Adjust as needed
        
    def start(self):
        """Start the UI on the MAIN thread (required for macOS)"""
        self.running = True
        self._run_ui()
        
    def stop(self):
        """Stop the UI"""
        self.running = False
        plt.close('all')
        
    def _run_ui(self):
        """Main UI loop - must run on main thread"""
        # Create base image (800x600 for the park map)
        width, height = 1400, 800
        
        # Define positions for park elements
        ride_positions = self._calculate_ride_positions()
        facility_positions = self._calculate_facility_positions()
        
        plt.ion()  # Turn on interactive mode
        fig = plt.figure(figsize=(14, 8))
        
        # Add window close event handler
        def on_window_close(event):
            """Handle window close event"""
            print("\n🛑 Window closed - stopping simulation...")
            self.running = False
            self.clock.stop()
            # Force exit the program
            os._exit(0)
        
        fig.canvas.mpl_connect('close_event', on_window_close)
        
        # Add "Exit Simulation" button
        ax_button = plt.axes([0.85, 0.02, 0.12, 0.04])  # [left, bottom, width, height]
        btn_exit = Button(ax_button, 'Exit Simulation', color='#ff6b6b', hovercolor='#ff5252')
        
        def on_exit_click(event):
            """Handle exit button click"""
            print("\n🛑 Exit button clicked - stopping simulation...")
            self.running = False
            self.clock.stop()
            plt.close('all')  # Close all figures
            # Force exit the program
            os._exit(0)
        
        btn_exit.on_clicked(on_exit_click)
        
        try:
            while self.running:
                current_time = self.clock.now()
                
                # Check if simulation time is complete (check earlier, at 479 to be safe)
                if current_time >= 479 or self.clock.should_stop():
                    print(f"\nSimulation approaching end at minute {current_time}...")
                    
                    # Draw final state
                    park_image = Image.new('RGB', (width, height), color='#90EE90')
                    draw = ImageDraw.Draw(park_image, 'RGBA')
                    
                    try:
                        self._draw_title(draw)
                        self._draw_capacity_bar(draw)
                        self._draw_rides(draw, ride_positions)
                        self._draw_facilities(draw, facility_positions)
                        self._draw_metrics(draw)
                    except Exception as draw_error:
                        print(f"Error drawing final state: {draw_error}")
                    
                    # Add "SIMULATION COMPLETE" message
                    try:
                        from PIL import ImageFont
                        font = ImageFont.truetype("arial.ttf", 48)
                    except:
                        font = None
                    
                    # Semi-transparent overlay
                    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 150))
                    draw_overlay = ImageDraw.Draw(overlay)
                    if font:
                        draw_overlay.text((400, 350), "SIMULATION COMPLETE", fill=(255, 255, 255, 255), font=font)
                    else:
                        draw_overlay.text((500, 350), "SIMULATION COMPLETE", fill=(255, 255, 255, 255))
                    
                    park_image = Image.alpha_composite(park_image.convert('RGBA'), overlay)
                    
                    # Display final state
                    plt.clf()
                    
                    # Draw the final park image
                    ax_main = plt.axes([0.05, 0.15, 0.9, 0.8])
                    ax_main.imshow(park_image)
                    ax_main.axis('off')
                    
                    # Re-add the close button for final screen
                    ax_button_final = plt.axes([0.4, 0.05, 0.2, 0.05])
                    btn_close = Button(ax_button_final, 'Close Window', color='#4CAF50', hovercolor='#45a049')
                    
                    def on_close_click(event):
                        print("\nClosing simulation window...")
                        self.running = False
                        plt.close('all')
                    
                    btn_close.on_clicked(on_close_click)
                    
                    plt.draw()
                    
                    print(f"Simulation ended at minute {current_time}")
                    print("Click 'Close Window' button or close the window to continue...")
                    
                    # Keep window open until button is clicked or window is closed
                    try:
                        plt.show(block=True)  # Block until window is closed
                    except:
                        pass
                    
                    self.running = False
                    break
                    
                # Create new image
                park_image = Image.new('RGB', (width, height), color='#90EE90')  # Light green background
                draw = ImageDraw.Draw(park_image, 'RGBA')
                
                # Draw title
                self._draw_title(draw)
                
                # Draw park capacity bar
                self._draw_capacity_bar(draw)
                
                # Draw rides
                self._draw_rides(draw, ride_positions)
                
                # Draw facilities (food, merch, bathrooms)
                self._draw_facilities(draw, facility_positions)
                
                # Draw metrics summary
                self._draw_metrics(draw)
                
                # Display the image
                plt.clf()
                
                # Draw the park image
                ax_main = plt.axes([0.05, 0.1, 0.9, 0.85])  # [left, bottom, width, height]
                ax_main.imshow(park_image)
                ax_main.axis('off')
                
                # Add the exit button
                ax_button = plt.axes([0.85, 0.02, 0.12, 0.04])
                btn_exit = Button(ax_button, 'Exit Simulation', color='#ff6b6b', hovercolor='#ff5252')
                btn_exit.on_clicked(on_exit_click)
                
                plt.draw()
                
                # Use non-blocking pause with timeout
                try:
                    plt.pause(0.5)  # Update every 0.5 seconds
                except:
                    # If window is closed, stop gracefully
                    self.running = False
                    break
                
        except Exception as e:
            print(f"UI Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("UI shutting down...")
            plt.close('all')
    
    def _calculate_ride_positions(self):
        """Calculate positions for rides on the map"""
        positions = {}
        # Arrange rides in a grid pattern in the center area
        rides_per_row = 3
        start_x = 150
        start_y = 150
        spacing_x = 250
        spacing_y = 180
        
        for i, ride in enumerate(self.rides):
            row = i // rides_per_row
            col = i % rides_per_row
            x = start_x + col * spacing_x
            y = start_y + row * spacing_y
            positions[ride.name] = {
                'center': (x, y),
                'size': (120, 100)
            }
        return positions
    
    def _calculate_facility_positions(self):
        """Calculate positions for facilities"""
        positions = {
            'food': [],
            'merch': [],
            'bathrooms': []
        }
        
        # Food trucks - top right
        for i, truck in enumerate(self.food_trucks):
            positions['food'].append({
                'name': truck.name,
                'pos': (1100, 100 + i * 35),
                'size': (30, 25)
            })
        
        # Merch stands - bottom right
        for i, stand in enumerate(self.merch_stands):
            positions['merch'].append({
                'name': stand.name,
                'pos': (1100, 400 + i * 35),
                'size': (30, 25)
            })
        
        # Bathrooms - bottom left (grid)
        for i, bathroom in enumerate(self.bathrooms):
            col = i % 5
            row = i // 5
            positions['bathrooms'].append({
                'name': bathroom.name,
                'pos': (50 + col * 35, 650 + row * 35),
                'size': (30, 30)
            })
        
        return positions
    
    def _draw_title(self, draw):
        """Draw the park title"""
        try:
            font = ImageFont.truetype("arial.ttf", 32)
        except:
            font = ImageFont.load_default()
        
        draw.text((500, 20), "🎢 AMUSEMENT PARK LIVE VIEW 🎡", fill="black", font=font)
        
        # Current time
        try:
            small_font = ImageFont.truetype("arial.ttf", 16)
        except:
            small_font = ImageFont.load_default()
        
        current_minute = self.clock.now()
        draw.text((550, 60), f"Time: {current_minute} minutes", fill="black", font=small_font)
    
    def _draw_capacity_bar(self, draw):
        """Draw park capacity progress bar"""
        total_visitors = self.park.get_total_visitors()
        capacity_percentage = min(100, (total_visitors / self.max_capacity) * 100)
        
        # Vertical bar on the left
        bar_x = 20
        bar_y_start = 100
        bar_height = 400
        bar_width = 40
        bar_fill_height = int((capacity_percentage / 100) * bar_height)
        
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        draw.text((bar_x - 5, bar_y_start - 30), "Park Capacity", fill="black", font=font)
        
        # Background
        draw.rectangle(
            [bar_x, bar_y_start, bar_x + bar_width, bar_y_start + bar_height],
            fill="gray"
        )
        
        # Filled part with color gradient
        color = self._value_to_color(capacity_percentage)
        draw.rectangle(
            [bar_x, bar_y_start + bar_height - bar_fill_height, 
             bar_x + bar_width, bar_y_start + bar_height],
            fill=color
        )
        
        # Percentage label
        draw.text((bar_x + 5, bar_y_start + bar_height + 10), 
                 f"{int(capacity_percentage)}%", fill="black", font=font)
        draw.text((bar_x - 10, bar_y_start + bar_height + 30), 
                 f"{total_visitors}/{self.max_capacity}", fill="black", font=font)
    
    def _draw_rides(self, draw, positions):
        """Draw all rides with their status"""
        try:
            font = ImageFont.truetype("arial.ttf", 11)
            small_font = ImageFont.truetype("arial.ttf", 9)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        for ride in self.rides:
            if ride.name not in positions:
                continue
                
            pos_data = positions[ride.name]
            center_x, center_y = pos_data['center']
            width, height = pos_data['size']
            
            # Get ride status
            state = ride.get_state_name()
            queue_size = ride.queue.size()
            total_riders = ride.get_total_riders()
            
            # Determine color based on state
            if state == "BROKEN":
                color = (200, 50, 50, 200)  # Red
            elif state == "MAINTENANCE":
                color = (200, 150, 50, 200)  # Orange
            elif state == "BOARDING":
                color = (50, 150, 200, 200)  # Blue
            else:  # OPEN
                color = (50, 200, 50, 200)  # Green
            
            # Draw ride rectangle
            x1 = center_x - width // 2
            y1 = center_y - height // 2
            x2 = center_x + width // 2
            y2 = center_y + height // 2
            
            draw.rectangle([x1, y1, x2, y2], fill=color, outline="black", width=2)
            
            # Draw ride name
            # Truncate long names
            display_name = ride.name[:12] if len(ride.name) > 12 else ride.name
            draw.text((center_x - 50, center_y - 35), display_name, fill="white", font=font)
            
            # Draw state
            draw.text((center_x - 40, center_y - 15), state, fill="white", font=small_font)
            
            # Draw queue size
            draw.text((center_x - 40, center_y + 5), f"Queue: {queue_size}", 
                     fill="white", font=small_font)
            
            # Draw total riders
            draw.text((center_x - 40, center_y + 20), f"Riders: {total_riders}", 
                     fill="white", font=small_font)
    
    def _draw_facilities(self, draw, positions):
        """Draw food trucks, merch stands, and bathrooms"""
        try:
            font = ImageFont.truetype("arial.ttf", 10)
        except:
            font = ImageFont.load_default()
        
        # Draw food trucks
        draw.text((1050, 75), "Food Trucks:", fill="black", font=font)
        for i, truck in enumerate(self.food_trucks):
            pos_data = positions['food'][i]
            x, y = pos_data['pos']
            w, h = pos_data['size']
            
            queue_size = truck.queue.size()
            is_busy = queue_size > 0
            color = (255, 100, 100, 180) if is_busy else (100, 255, 100, 180)
            
            draw.rectangle([x, y, x + w, y + h], fill=color, outline="black", width=1)
            draw.text((x + w + 5, y), f"{truck.name} ({queue_size})", 
                     fill="black", font=font)
        
        # Draw merch stands
        draw.text((1050, 375), "Merch Stands:", fill="black", font=font)
        for i, stand in enumerate(self.merch_stands):
            pos_data = positions['merch'][i]
            x, y = pos_data['pos']
            w, h = pos_data['size']
            
            queue_size = stand.queue.size()
            is_busy = queue_size > 0
            color = (255, 100, 255, 180) if is_busy else (200, 150, 255, 180)
            
            draw.rectangle([x, y, x + w, y + h], fill=color, outline="black", width=1)
            draw.text((x + w + 5, y), f"{stand.name} ({queue_size})", 
                     fill="black", font=font)
        
        # Draw bathrooms
        draw.text((50, 625), "Bathrooms:", fill="black", font=font)
        for i, bathroom in enumerate(self.bathrooms):
            pos_data = positions['bathrooms'][i]
            x, y = pos_data['pos']
            w, h = pos_data['size']
            
            # Check if bathroom is occupied (has someone in queue or lock is held)
            is_occupied = bathroom.queue.size() > 0
            color = (150, 150, 200, 180) if is_occupied else (200, 200, 255, 180)
            
            draw.rectangle([x, y, x + w, y + h], fill=color, outline="black", width=1)
    
    def _draw_metrics(self, draw):
        """Draw summary metrics"""
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        summary = self.metrics.get_summary()
        
        # Metrics panel
        panel_x = 900
        panel_y = 600
        
        draw.rectangle([panel_x - 10, panel_y - 10, panel_x + 450, panel_y + 180], 
                      fill=(255, 255, 200, 220), outline="black", width=2)
        
        draw.text((panel_x, panel_y), "📊 PARK STATISTICS", fill="black", font=font)
        
        metrics_text = [
            f"Total Visitors: {summary['total_visitors']}",
            f"Visitors Left: {summary['total_exits']}",
            f"Food Revenue: ${summary['total_food_revenue']:.2f}",
            f"Merch Revenue: ${summary['total_merch_revenue']:.2f}",
            f"Total Revenue: ${summary['total_revenue']:.2f}",
        ]
        
        y_offset = 25
        for text in metrics_text:
            draw.text((panel_x, panel_y + y_offset), text, fill="black", font=font)
            y_offset += 25
        
        # Most popular ride
        if summary['ride_counts']:
            most_popular = max(summary['ride_counts'].items(), key=lambda x: x[1])
            draw.text((panel_x, panel_y + y_offset), 
                     f"Most Popular: {most_popular[0]} ({most_popular[1]} rides)", 
                     fill="blue", font=font)
    
    def _value_to_color(self, value, min_value=0, max_value=100):
        """Convert value to RGB color (green to red gradient)"""
        value = max(min_value, min(max_value, value))
        ratio = (value - min_value) / (max_value - min_value)
        r = int(255 * ratio)
        g = int(255 * (1 - ratio))
        b = 0
        return (r, g, b, 255)
