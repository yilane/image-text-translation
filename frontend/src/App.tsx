import React, { useState } from 'react'
import { Upload, Button, message, Card, Image, Typography, Space, Divider } from 'antd'
import { InboxOutlined, UploadOutlined } from '@ant-design/icons'
import type { UploadProps } from 'antd'
import './App.css'

const { Dragger } = Upload
const { Title, Text } = Typography

interface UploadResponse {
  success: boolean
  message: string
  data: {
    file_id: string
    history_id: number
    file_path: string
    file_size: number
    image_info: {
      width: number
      height: number
      format: string
      mode: string
      size_bytes: number
    }
  }
}

function App() {
  const [uploadedFile, setUploadedFile] = useState<any>(null)
  const [uploading, setUploading] = useState(false)

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.jpg,.jpeg,.png,.bmp,.tiff,.webp',
    action: 'http://localhost:8000/api/upload',
    onChange(info) {
      const { status } = info.file
      if (status === 'uploading') {
        setUploading(true)
      }
      if (status === 'done') {
        setUploading(false)
        const response: UploadResponse = info.file.response
        if (response.success) {
          message.success(`${info.file.name} 文件上传成功`)
          setUploadedFile({
            name: info.file.name,
            url: `http://localhost:8000/${response.data.file_path}`,
            info: response.data
          })
        } else {
          message.error(`${info.file.name} 文件上传失败`)
        }
      } else if (status === 'error') {
        setUploading(false)
        message.error(`${info.file.name} 文件上传失败`)
      }
    },
    beforeUpload(file) {
      const isImage = file.type.startsWith('image/')
      if (!isImage) {
        message.error('只能上传图片文件!')
        return false
      }
      const isLt10M = file.size / 1024 / 1024 < 10
      if (!isLt10M) {
        message.error('图片大小必须小于 10MB!')
        return false
      }
      return true
    },
  }

  return (
    <div className="app">
      <div className="container">
        <Title level={1} style={{ textAlign: 'center', marginBottom: '2rem' }}>
          🌐 图片文字翻译工具
        </Title>
        
        <Card title="📤 上传图片" style={{ marginBottom: '2rem' }}>
          <Dragger {...uploadProps} style={{ padding: '2rem' }}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
            </p>
            <p className="ant-upload-text">
              点击或拖拽图片到此区域上传
            </p>
            <p className="ant-upload-hint">
              支持 PNG、JPG、JPEG、BMP、TIFF、WebP 格式，文件大小不超过 10MB
            </p>
          </Dragger>
        </Card>

        {uploadedFile && (
          <Card title="📷 图片预览" style={{ marginBottom: '2rem' }}>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div style={{ textAlign: 'center' }}>
                <Image
                  width={400}
                  src={uploadedFile.url}
                  alt={uploadedFile.name}
                  style={{ maxWidth: '100%' }}
                />
              </div>
              
              <Divider />
              
              <div>
                <Title level={4}>📊 文件信息</Title>
                <Space direction="vertical">
                  <Text><strong>文件名:</strong> {uploadedFile.name}</Text>
                  <Text><strong>尺寸:</strong> {uploadedFile.info.image_info.width} × {uploadedFile.info.image_info.height}</Text>
                  <Text><strong>格式:</strong> {uploadedFile.info.image_info.format}</Text>
                  <Text><strong>大小:</strong> {(uploadedFile.info.file_size / 1024 / 1024).toFixed(2)} MB</Text>
                </Space>
              </div>

              <Divider />
              
              <div style={{ textAlign: 'center' }}>
                <Space>
                  <Button type="primary" icon={<UploadOutlined />} disabled>
                    开始翻译 (即将推出)
                  </Button>
                  <Button 
                    onClick={() => setUploadedFile(null)}
                  >
                    重新上传
                  </Button>
                </Space>
              </div>
            </Space>
          </Card>
        )}

        <Card title="ℹ️ 使用说明">
          <Space direction="vertical">
            <Text>1. 支持多种图片格式：PNG、JPG、JPEG、BMP、TIFF、WebP</Text>
            <Text>2. 图片大小限制：最大 10MB</Text>
            <Text>3. 上传后可预览图片信息</Text>
            <Text>4. 翻译功能正在开发中...</Text>
          </Space>
        </Card>
      </div>
    </div>
  )
}

export default App
