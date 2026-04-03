import React, { useState, useRef } from 'react';
import './UploadSection.css';
import axios from 'axios';
import { toast } from 'react-toastify';
import { MdCloudUpload, MdImage } from 'react-icons/md';

function UploadSection({ setResult, setLoading, loading }) {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const fileInputRef = useRef(null);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      setPreview(URL.createObjectURL(file));
      setResult(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setImage(file);
      setPreview(URL.createObjectURL(file));
      setResult(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleSubmit = async () => {
    if (!image) {
      toast.error('Please select an image first!');
      return;
    }

    const formData = new FormData();
    formData.append('image', image);

    try {
      setLoading(true);
      const response = await axios.post(
        'http://127.0.0.1:5000/api/validate',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      setResult(response.data);
      toast.success('Image processed successfully!');
    } catch (error) {
      const msg = error.response?.data?.error || 'Something went wrong!';
  console.log('Full error:', error.response?.data);
  toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setImage(null);
    setPreview(null);
    setResult(null);
    fileInputRef.current.value = '';
  };

  return (
    <div className="upload-section">
      <h2>Upload Envelope Image</h2>

      <div
        className="drop-zone"
        onClick={() => fileInputRef.current.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        {preview ? (
          <img src={preview} alt="Preview" className="preview-img" />
        ) : (
          <div className="drop-placeholder">
            <MdCloudUpload size={60} color="#f97316" />
            <p>Drag & drop or click to upload</p>
            <span>Supports JPG, PNG, JPEG</span>
          </div>
        )}
      </div>

      <input
        type="file"
        accept="image/*"
        ref={fileInputRef}
        onChange={handleImageChange}
        style={{ display: 'none' }}
      />

      <div className="upload-buttons">
        <button
          className="btn-upload"
          onClick={() => fileInputRef.current.click()}
        >
          <MdImage size={20} />
          Choose Image
        </button>

        <button
          className="btn-validate"
          onClick={handleSubmit}
          disabled={loading || !image}
        >
          {loading ? (
            <span className="spinner"></span>
          ) : (
            '🔍 Validate PIN'
          )}
        </button>

        {image && (
          <button className="btn-clear" onClick={handleClear}>
            ✕ Clear
          </button>
        )}
      </div>
    </div>
  );
}

export default UploadSection;