from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import io
from datetime import datetime

app = Flask(__name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ('csv', 'xlsx')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_common_columns', methods=['POST'])
def get_common_columns():
    if 'file1' not in request.files or 'file2' not in request.files:
        return jsonify({'error': 'Both files are required'}), 400
        
    file1 = request.files['file1']
    file2 = request.files['file2']
    
    if not (file1 and file2 and allowed_file(file1.filename) and allowed_file(file2.filename)):
        return jsonify({'error': 'Formato inválido: Solo se aceptan csv o xlsx'}), 400
    
    df1 = pd.read_csv(file1) if file1.filename.endswith('.csv') else pd.read_excel(file1)
    df2 = pd.read_csv(file2) if file2.filename.endswith('.csv') else pd.read_excel(file2)
    
    try:
        common_columns = list(set(df1.columns) & set(df2.columns))
        return jsonify({'columns': common_columns})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/merge_files', methods=['POST'])
def merge_files():
    if 'file1' not in request.files or 'file2' not in request.files:
        return jsonify({'error': 'Both files are required'}), 400
    
    file1 = request.files['file1']
    file2 = request.files['file2']
    
    if not (file1 and file2 and allowed_file(file1.filename) and allowed_file(file2.filename)):
        return jsonify({'error': 'Formato inválido: Solo se aceptan csv o xlsx'}), 400
    
    merge_columns = request.form.getlist('columns[]')
    if not merge_columns:
        return jsonify({'error': 'At least one merge column is required'}), 400
    
    try:
        
        if file1.filename.endswith('.csv'):
            df1 = pd.read_csv(file1, low_memory=True)
        else:
            df1 = pd.read_excel(file1)
            
        if file2.filename.endswith('.csv'):
            df2 = pd.read_csv(file2, low_memory=True)
        else:
            df2 = pd.read_excel(file2)
        
        for column in merge_columns:
            if column not in df1.columns or column not in df2.columns:
                return jsonify({'error': f'Column "{column}" not found in both files'}), 400
        
        merged_df = pd.merge(df1, df2, on=merge_columns, how='inner')
        
        output = io.BytesIO()
        
        merged_df.to_csv(output, index=False)
        output.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"merged_data_{timestamp}.csv"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        app.logger.error(f"Error during merge: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)