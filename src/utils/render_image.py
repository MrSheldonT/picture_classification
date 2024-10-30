from flask import Flask, send_file, jsonify
import os


def render_image(image_path):
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/jpeg')
    else:
        return jsonify({'status': 'error', 'message': 'Archivo no encontrado en el servidor'})
