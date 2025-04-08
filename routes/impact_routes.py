import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from config import logger, UPLOAD_FOLDER
from utils.file_utils import allowed_file, generate_unique_filename
from services.impact_service import process_impact_files, calculate_impact, simulate_budget_change
import json

impact = Blueprint('impact', __name__)

@impact.route('/impact')
def index():
    """Render the impact analysis upload page."""
    return render_template('impact_upload.html')

@impact.route('/impact/upload', methods=['POST'])
def upload_files():
    """Handle multiple file uploads for impact analysis."""
    if 'files[]' not in request.files:
        flash('No files part')
        return redirect(url_for('impact.index'))
    
    files = request.files.getlist('files[]')
    
    if not files or files[0].filename == '':
        flash('No selected files')
        return redirect(url_for('impact.index'))
    
    # Store file information
    uploaded_files = []
    
    for file in files:
        if file and allowed_file(file.filename):
            # Generate a unique filename
            unique_filename = generate_unique_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(file_path)
            
            uploaded_files.append({
                'original_name': file.filename,
                'path': file_path
            })
    
    if not uploaded_files:
        flash('No valid files uploaded. Please upload CSV files.')
        return redirect(url_for('impact.index'))
    
    try:
        # Process all uploaded files
        impact_data = process_impact_files(uploaded_files)
        
        # Store the impact data in session
        session['impact_data'] = json.dumps(impact_data)
        
        # Store paths to clean up later
        session['impact_file_paths'] = [f['path'] for f in uploaded_files]
        
        return redirect(url_for('impact.dashboard'))
        
    except Exception as e:
        # Clean up files on error
        for file_info in uploaded_files:
            if os.path.exists(file_info['path']):
                os.remove(file_info['path'])
                
        error_message = f'Error processing files: {str(e)}'
        logger.error(error_message)
        flash(error_message)
        return redirect(url_for('impact.index'))

@impact.route('/impact/dashboard')
def dashboard():
    """Render the impact analysis dashboard."""
    if 'impact_data' not in session:
        flash('No impact data available. Please upload files first.')
        return redirect(url_for('impact.index'))
    
    try:
        impact_data = json.loads(session['impact_data'])
        return render_template('impact_dashboard.html', impact_data=impact_data)
    except Exception as e:
        error_message = f'Error loading impact data: {str(e)}'
        logger.error(error_message)
        flash(error_message)
        return redirect(url_for('impact.index'))

@impact.route('/impact/simulate', methods=['POST'])
def simulate():
    """Simulate budget changes and return updated impact data."""
    if 'impact_data' not in session:
        return jsonify({'error': 'No impact data available'}), 400
    
    try:
        impact_data = json.loads(session['impact_data'])
        budget_changes = request.json.get('budget_changes', {})
        
        # Calculate new impact based on budget changes
        updated_data = simulate_budget_change(impact_data, budget_changes)
        
        return jsonify(updated_data)
    except Exception as e:
        logger.error(f'Error in simulation: {str(e)}')
        return jsonify({'error': str(e)}), 500

@impact.route('/impact/cleanup', methods=['POST'])
def cleanup():
    """Clean up uploaded files when done with analysis."""
    if 'impact_file_paths' in session:
        for file_path in session['impact_file_paths']:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        session.pop('impact_file_paths', None)
        session.pop('impact_data', None)
    
    return jsonify({'status': 'success'})