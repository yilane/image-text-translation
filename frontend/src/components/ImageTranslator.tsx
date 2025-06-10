import React, { useState } from 'react'
import { 
  Upload, Button, message, Card, Image, Typography, Space, Divider, 
  Select, Progress, Spin, Result, Row, Col, Steps, Alert, Tag 
} from 'antd'
import { 
  InboxOutlined, TranslationOutlined, EyeOutlined, DownloadOutlined,
  SettingOutlined, HistoryOutlined 
} from '@ant-design/icons'
import type { UploadProps } from 'antd'

const { Dragger } = Upload
const { Title, Text, Paragraph } = Typography
const { Option } = Select
const { Step } = Steps

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

interface TranslationResult {
  success: boolean
  data: {
    output_image_path: string
    translation_results: Array<{
      id: number
      bbox: number[][]
      confidence: number
      original_text: string
      translated_text: string
    }>
    processing_info: {
      total_regions: number
      source_language: string
      target_language: string
      provider: string
      min_confidence: number
    }
  }
}

const ImageTranslator: React.FC = () => {
  const [uploadedFile, setUploadedFile] = useState<any>(null)
  const [uploading, setUploading] = useState(false)
  const [translating, setTranslating] = useState(false)
  const [translationResult, setTranslationResult] = useState<TranslationResult | null>(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [targetLanguage, setTargetLanguage] = useState('en')
  const [sourceLanguage, setSourceLanguage] = useState('auto')
  const [provider, setProvider] = useState('openai')
  const [minConfidence, setMinConfidence] = useState(0.5)

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
          setCurrentStep(1)
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

  const handleTranslate = async () => {
    if (!uploadedFile) {
      message.error('请先上传图片')
      return
    }

    setTranslating(true)
    setCurrentStep(2)

    try {
      const formData = new FormData()
      
      // 重新上传文件进行翻译
      const response = await fetch(uploadedFile.url)
      const blob = await response.blob()
      const file = new File([blob], uploadedFile.name, { type: blob.type })
      
      formData.append('file', file)
      formData.append('target_language', targetLanguage)
      formData.append('source_language', sourceLanguage)
      formData.append('provider', provider)
      formData.append('min_confidence', minConfidence.toString())

      const translateResponse = await fetch('http://localhost:8000/api/process/translate-image', {
        method: 'POST',
        body: formData,
      })

      const result: TranslationResult = await translateResponse.json()

      if (result.success) {
        setTranslationResult(result)
        setCurrentStep(3)
        message.success('翻译完成！')
      } else {
        throw new Error('翻译失败')
      }
    } catch (error) {
      console.error('Translation error:', error)
      message.error('翻译过程中发生错误，请重试')
      setCurrentStep(1)
    } finally {
      setTranslating(false)
    }
  }

  const handleReset = () => {
    setUploadedFile(null)
    setTranslationResult(null)
    setCurrentStep(0)
  }

  const languages = [
    { value: 'auto', label: '自动检测' },
    { value: 'zh', label: '中文' },
    { value: 'en', label: '英文' },
    { value: 'ja', label: '日文' },
    { value: 'ko', label: '韩文' },
    { value: 'fr', label: '法文' },
    { value: 'de', label: '德文' },
    { value: 'es', label: '西班牙文' },
    { value: 'ru', label: '俄文' },
  ]

  const providers = [
    { value: 'openai', label: 'OpenAI' },
    { value: 'baidu', label: '百度翻译' },
    { value: 'google', label: 'Google翻译' },
  ]

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Title level={1} style={{ textAlign: 'center', marginBottom: '2rem' }}>
        🌐 智能图片文字翻译工具
      </Title>

      <Steps current={currentStep} style={{ marginBottom: '2rem' }}>
        <Step title="上传图片" icon={<InboxOutlined />} />
        <Step title="配置翻译" icon={<SettingOutlined />} />
        <Step title="处理翻译" icon={<TranslationOutlined />} />
        <Step title="查看结果" icon={<EyeOutlined />} />
      </Steps>

      {currentStep === 0 && (
        <Card title="📤 上传图片">
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
      )}

      {currentStep >= 1 && uploadedFile && (
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={12}>
            <Card title="📷 原始图片">
              <div style={{ textAlign: 'center' }}>
                <Image
                  width="100%"
                  src={uploadedFile.url}
                  alt={uploadedFile.name}
                  style={{ maxHeight: '400px', objectFit: 'contain' }}
                />
              </div>
              <Divider />
              <Space direction="vertical">
                <Text><strong>文件名:</strong> {uploadedFile.name}</Text>
                <Text><strong>尺寸:</strong> {uploadedFile.info.image_info.width} × {uploadedFile.info.image_info.height}</Text>
                <Text><strong>格式:</strong> {uploadedFile.info.image_info.format}</Text>
                <Text><strong>大小:</strong> {(uploadedFile.info.file_size / 1024 / 1024).toFixed(2)} MB</Text>
              </Space>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="⚙️ 翻译配置">
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <div>
                  <Text strong>源语言：</Text>
                  <Select
                    value={sourceLanguage}
                    onChange={setSourceLanguage}
                    style={{ width: '100%', marginTop: '8px' }}
                  >
                    {languages.map(lang => (
                      <Option key={lang.value} value={lang.value}>{lang.label}</Option>
                    ))}
                  </Select>
                </div>

                <div>
                  <Text strong>目标语言：</Text>
                  <Select
                    value={targetLanguage}
                    onChange={setTargetLanguage}
                    style={{ width: '100%', marginTop: '8px' }}
                  >
                    {languages.filter(lang => lang.value !== 'auto').map(lang => (
                      <Option key={lang.value} value={lang.value}>{lang.label}</Option>
                    ))}
                  </Select>
                </div>

                <div>
                  <Text strong>翻译服务：</Text>
                  <Select
                    value={provider}
                    onChange={setProvider}
                    style={{ width: '100%', marginTop: '8px' }}
                  >
                    {providers.map(p => (
                      <Option key={p.value} value={p.value}>{p.label}</Option>
                    ))}
                  </Select>
                </div>

                <div>
                  <Text strong>置信度阈值：{minConfidence}</Text>
                  <input
                    type="range"
                    min="0.1"
                    max="1"
                    step="0.1"
                    value={minConfidence}
                    onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
                    style={{ width: '100%', marginTop: '8px' }}
                  />
                </div>

                <Divider />

                <Space>
                  <Button
                    type="primary"
                    icon={<TranslationOutlined />}
                    onClick={handleTranslate}
                    loading={translating}
                    size="large"
                  >
                    开始翻译
                  </Button>
                  <Button onClick={handleReset}>重新开始</Button>
                </Space>
              </Space>
            </Card>
          </Col>
        </Row>
      )}

      {currentStep === 2 && (
        <Card title="🔄 正在处理">
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <Spin size="large" />
            <Paragraph style={{ marginTop: '1rem' }}>
              正在进行OCR识别和文字翻译，请稍候...
            </Paragraph>
            <Progress percent={75} status="active" />
          </div>
        </Card>
      )}

      {currentStep === 3 && translationResult && (
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={12}>
            <Card title="✨ 翻译结果">
              <div style={{ textAlign: 'center' }}>
                <Image
                  width="100%"
                  src={`http://localhost:8000/${translationResult.data.output_image_path}`}
                  alt="翻译结果"
                  style={{ maxHeight: '400px', objectFit: 'contain' }}
                />
              </div>
              <Divider />
              <div style={{ textAlign: 'center' }}>
                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  href={`http://localhost:8000/${translationResult.data.output_image_path}`}
                  download
                >
                  下载翻译图片
                </Button>
              </div>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="📊 翻译详情">
              <Space direction="vertical" style={{ width: '100%' }}>
                <Alert
                  message={`成功翻译 ${translationResult.data.processing_info.total_regions} 个文字区域`}
                  type="success"
                  showIcon
                />
                
                <div>
                  <Tag color="blue">源语言: {translationResult.data.processing_info.source_language}</Tag>
                  <Tag color="green">目标语言: {translationResult.data.processing_info.target_language}</Tag>
                  <Tag color="orange">服务商: {translationResult.data.processing_info.provider}</Tag>
                </div>

                <Divider orientation="left">翻译对照</Divider>

                <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                  {translationResult.data.translation_results.map((result, index) => (
                    <Card key={index} size="small" style={{ marginBottom: '8px' }}>
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Text strong>区域 {index + 1} (置信度: {(result.confidence * 100).toFixed(1)}%)</Text>
                        <Text>原文: {result.original_text}</Text>
                        <Text type="success">译文: {result.translated_text}</Text>
                      </Space>
                    </Card>
                  ))}
                </div>

                <Divider />

                <Space>
                  <Button onClick={handleReset}>翻译新图片</Button>
                  <Button icon={<HistoryOutlined />}>查看历史</Button>
                </Space>
              </Space>
            </Card>
          </Col>
        </Row>
      )}
    </div>
  )
}

export default ImageTranslator 