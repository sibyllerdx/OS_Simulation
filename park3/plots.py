"""
Plotting Module for Park Simulation
====================================
Generates various plots and visualizations from simulation metrics.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import os
from typing import Optional
import numpy as np


def generate_plots(metrics, output_dir: str = "output"):
    """
    Generate all plots from metrics data and save to output directory.
    
    Args:
        metrics: Metrics instance with simulation data
        output_dir: Directory to save plot images
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get analysis data from metrics
    data = metrics.get_analysis_data()
    
    print(f"\n{'='*60}")
    print("GENERATING PLOTS")
    print(f"{'='*60}")
    
    # Generate each plot
    _plot_avg_wait_time_per_ride(data, output_dir)
    _plot_population_over_time(data, output_dir)
    _plot_revenue_per_facility(data, output_dir)
    _plot_rides_per_attraction(data, output_dir)
    _plot_rides_per_visitor(data, output_dir)
    _plot_spending_vs_time(data, output_dir)
    _plot_time_per_visitor(data, output_dir)
    
    print(f"\n✓ All plots saved to '{output_dir}/' directory")
    print(f"{'='*60}\n")


def _plot_avg_wait_time_per_ride(data, output_dir):
    """Plot: Average wait time in minutes per each of the 9 rides"""
    avg_wait_times = data['avg_wait_times']
    
    if not avg_wait_times:
        print("  ⊘ Skipping avg_wait_time_per_ride.png (no data)")
        return
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Sort by ride name for consistency
    rides = sorted(avg_wait_times.keys())
    wait_times = [avg_wait_times[r] for r in rides]
    
    x_pos = np.arange(len(rides))
    bars = ax.bar(x_pos, wait_times, color='coral', edgecolor='black', linewidth=1.5)
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{height:.1f} min',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.set_xlabel('Ride Name', fontsize=14, fontweight='bold')
    ax.set_ylabel('Average Wait Time (minutes)', fontsize=14, fontweight='bold')
    ax.set_title('Average Wait Time Per Ride', fontsize=16, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(rides, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    
    filepath = os.path.join(output_dir, 'avg_wait_time_per_ride.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ Saved avg_wait_time_per_ride.png")


def _plot_population_over_time(data, output_dir):
    """Plot: Number of visitors in park over 480 minutes"""
    population_over_time = data['population_over_time']
    max_time = data['max_time']
    
    if not population_over_time:
        print("  ⊘ Skipping population_over_time.png (no data)")
        return
    
    fig, ax = plt.subplots(figsize=(16, 7))
    
    minutes = [p[0] for p in population_over_time]
    population = [p[1] for p in population_over_time]
    
    ax.plot(minutes, population, color='#2E86AB', linewidth=2.5)
    ax.fill_between(minutes, population, alpha=0.3, color='#2E86AB')
    
    # Set x-axis to show 0-480 minutes
    ax.set_xlim(0, max(480, max_time) if max_time > 0 else 480)
    ax.set_ylim(0, max(population) * 1.1 if population else 100)
    
    ax.set_xlabel('Simulation Time (minutes)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Number of Visitors in Park', fontsize=14, fontweight='bold')
    ax.set_title('Park Population Over Time', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Add tick marks every 60 minutes
    ax.set_xticks(range(0, int(ax.get_xlim()[1]) + 1, 60))
    
    plt.tight_layout()
    
    filepath = os.path.join(output_dir, 'population_over_time.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ Saved population_over_time.png")


def _plot_revenue_per_facility(data, output_dir):
    """Plot: Revenue in dollars per each merch stand and food truck"""
    facility_revenue = data['facility_revenue']
    
    if not facility_revenue:
        print("  ⊘ Skipping revenue_per_facility.png (no data)")
        return
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Sort by revenue (highest to lowest)
    sorted_facilities = sorted(facility_revenue.items(), key=lambda x: x[1], reverse=True)
    facilities = [f[0] for f in sorted_facilities]
    revenues = [f[1] for f in sorted_facilities]
    
    x_pos = np.arange(len(facilities))
    bars = ax.bar(x_pos, revenues, color='#FFD700', edgecolor='black', linewidth=1.5)
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + max(revenues) * 0.01,
                f'${height:.2f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.set_xlabel('Facility Name', fontsize=14, fontweight='bold')
    ax.set_ylabel('Total Revenue ($)', fontsize=14, fontweight='bold')
    ax.set_title('Revenue Per Facility (Food Trucks & Merch Stands)', fontsize=16, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(facilities, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    
    filepath = os.path.join(output_dir, 'revenue_per_facility.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ Saved revenue_per_facility.png")


def _plot_rides_per_attraction(data, output_dir):
    """Plot: Number of times each ride completed a round"""
    ride_counts = data['ride_counts']
    
    if not ride_counts:
        print("  ⊘ Skipping rides_per_attraction.png (no data)")
        return
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Sort by ride name for consistency
    rides = sorted(ride_counts.keys())
    counts = [ride_counts[r] for r in rides]
    
    x_pos = np.arange(len(rides))
    bars = ax.bar(x_pos, counts, color='steelblue', edgecolor='black', linewidth=1.5)
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + max(counts) * 0.01,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.set_xlabel('Ride Name', fontsize=14, fontweight='bold')
    ax.set_ylabel('Number of Completed Rounds', fontsize=14, fontweight='bold')
    ax.set_title('Rides Completed Per Attraction', fontsize=16, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(rides, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    
    filepath = os.path.join(output_dir, 'rides_per_attraction.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ Saved rides_per_attraction.png")


def _plot_rides_per_visitor(data, output_dir):
    """Plot: Each visitor on X-axis, number of rides on Y-axis (sorted least to most)"""
    visitor_rides_taken = data['visitor_rides_taken']
    visitor_ids = data['visitor_ids']
    
    if not visitor_rides_taken:
        print("  ⊘ Skipping rides_per_visitor.png (no data)")
        return
    
    fig, ax = plt.subplots(figsize=(16, 7))
    
    # Sort visitors by number of rides taken (least to most)
    sorted_data = sorted(zip(visitor_ids, visitor_rides_taken), key=lambda x: x[1])
    sorted_visitor_ids = [v[0] for v in sorted_data]
    sorted_rides_taken = [v[1] for v in sorted_data]
    
    # Create bars for each visitor
    x_pos = np.arange(len(sorted_visitor_ids))
    bars = ax.bar(x_pos, sorted_rides_taken, color='teal', edgecolor='black', linewidth=0.5, alpha=0.8)
    
    ax.set_xlabel('Visitor ID (sorted by rides taken)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Number of Rides Taken', fontsize=14, fontweight='bold')
    ax.set_title('Rides Per Visitor (Sorted Least to Most)', fontsize=16, fontweight='bold')
    
    # Only show visitor IDs at intervals to avoid clutter
    tick_interval = max(1, len(sorted_visitor_ids) // 20)
    ax.set_xticks(x_pos[::tick_interval])
    ax.set_xticklabels(sorted_visitor_ids[::tick_interval], rotation=45, ha='right')
    
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add average line
    if sorted_rides_taken:
        avg_rides = sum(sorted_rides_taken) / len(sorted_rides_taken)
        ax.axhline(avg_rides, color='red', linestyle='--', linewidth=2,
                   label=f'Average: {avg_rides:.1f} rides')
        ax.legend(fontsize=12)
    
    plt.tight_layout()
    
    filepath = os.path.join(output_dir, 'rides_per_visitor.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ Saved rides_per_visitor.png")


def _plot_spending_vs_time(data, output_dir):
    """Plot: Visitor spending (Y) vs time spent in park (X)"""
    spend_vs_time = data['spend_vs_time']
    
    if not spend_vs_time:
        print("  ⊘ Skipping spending_vs_time.png (no data)")
        return
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    times = [p[0] for p in spend_vs_time]
    spends = [p[1] for p in spend_vs_time]
    
    scatter = ax.scatter(times, spends, alpha=0.6, s=60, 
                        c=spends, cmap='viridis', edgecolors='black', linewidth=0.5)
    
    ax.set_xlabel('Time Spent in Park (minutes)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Money Spent ($)', fontsize=14, fontweight='bold')
    ax.set_title('Visitor Spending vs Time in Park', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Money Spent ($)', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    
    filepath = os.path.join(output_dir, 'spending_vs_time.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ Saved spending_vs_time.png")


def _plot_time_per_visitor(data, output_dir):
    """Plot: Each visitor on X-axis, time in park on Y-axis (sorted least to most)"""
    visitor_time_data = data['visitor_time_sorted']
    
    if not visitor_time_data:
        print("  ⊘ Skipping time_per_visitor.png (no data)")
        return
    
    fig, ax = plt.subplots(figsize=(16, 7))
    
    visitor_ids = [v[0] for v in visitor_time_data]
    times = [v[1] for v in visitor_time_data]
    
    x_pos = np.arange(len(visitor_ids))
    bars = ax.bar(x_pos, times, color='purple', edgecolor='black', linewidth=0.5, alpha=0.8)
    
    ax.set_xlabel('Visitor ID (sorted by time spent)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Time in Park (minutes)', fontsize=14, fontweight='bold')
    ax.set_title('Time Spent in Park Per Visitor (Sorted Least to Most)', fontsize=16, fontweight='bold')
    
    # Only show visitor IDs at intervals to avoid clutter
    tick_interval = max(1, len(visitor_ids) // 20)
    ax.set_xticks(x_pos[::tick_interval])
    ax.set_xticklabels(visitor_ids[::tick_interval], rotation=45, ha='right')
    
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add average line
    if times:
        avg_time = sum(times) / len(times)
        ax.axhline(avg_time, color='red', linestyle='--', linewidth=2,
                   label=f'Average: {avg_time:.1f} min')
        ax.legend(fontsize=12)
    
    plt.tight_layout()
    
    filepath = os.path.join(output_dir, 'time_per_visitor.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ Saved time_per_visitor.png")

