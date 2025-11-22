// API基础URL
            const API_BASE_URL = 'http://127.0.0.1:5000';

            let enhancementAvailable = false;

            document.addEventListener('DOMContentLoaded', function() {
                const imageFileInput = document.getElementById('imageFile');
                const fileLabel = document.getElementById('fileLabel');
                const fileLabelText = document.getElementById('fileLabelText');
                const processBtn = document.getElementById('processBtn');
                const loadingDiv = document.getElementById('loading');
                const loadingSteps = document.getElementById('loadingSteps');
                const resultsDiv = document.getElementById('results');
                const textResultTextarea = document.getElementById('textResult');
                const processingInfoDiv = document.getElementById('processingInfo');
                const errorDiv = document.getElementById('error');

                // 处理选项
                const useEnhancementCheckbox = document.getElementById('useEnhancement');
                const useDewarpCheckbox = document.getElementById('useDewarp');
                const enhancementWarning = document.getElementById('enhancementWarning');
                const enhancementItem = document.getElementById('enhancementItem');

                // 可视化图像和模态框
                const visualizationImage = document.getElementById('visualizationImage');
                const imageModal = document.getElementById('imageModal');
                const modalImage = document.getElementById('modalImage');
                const closeModal = document.querySelector('.close-modal');

                // 文本操作按钮
                const copyBtn = document.getElementById('copyBtn');
                const copyBtnText = document.getElementById('copyBtnText');
                const clearBtn = document.getElementById('clearBtn');

                // 复制功能
                copyBtn.addEventListener('click', function() {
                    const text = textResultTextarea.value;
                    if (!text.trim()) {
                        showToast('没有可复制的内容', 'error');
                        return;
                    }

                    // 使用现代的剪贴板API
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        navigator.clipboard.writeText(text).then(function() {
                            showCopySuccess();
                        }).catch(function() {
                            // 如果现代API失败，使用传统方法
                            fallbackCopyTextToClipboard(text);
                        });
                    } else {
                        // 使用传统的复制方法
                        fallbackCopyTextToClipboard(text);
                    }
                });


                // 传统的复制方法（兼容旧浏览器）
                function fallbackCopyTextToClipboard(text) {
                    textResultTextarea.select();
                    textResultTextarea.setSelectionRange(0, 99999); // 移动端兼容

                    try {
                        const successful = document.execCommand('copy');
                        if (successful) {
                            showCopySuccess();
                        } else {
                            showToast('复制失败，请手动选择文本复制', 'error');
                        }
                    } catch (err) {
                        showToast('复制失败，请手动选择文本复制', 'error');
                    }

                    // 取消选择
                    if (window.getSelection) {
                        window.getSelection().removeAllRanges();
                    }
                }

                // 显示复制成功状态
                function showCopySuccess() {
                    // 更改按钮状态
                    copyBtn.classList.add('copied');
                    copyBtnText.textContent = '已复制';
                    
                    // 显示成功提示
                    showToast('文本已复制到剪贴板 ✨');

                    // 2秒后恢复按钮状态
                    setTimeout(function() {
                        copyBtn.classList.remove('copied');
                        copyBtnText.textContent = '复制文本';
                    }, 2000);
                }

                // 显示Toast通知
                function showToast(message, type = 'success') {
                    // 移除已存在的toast
                    const existingToast = document.querySelector('.toast');
                    if (existingToast) {
                        existingToast.remove();
                    }

                    // 创建新的toast
                    const toast = document.createElement('div');
                    toast.className = `toast ${type}`;
                    toast.innerHTML = `
                        <span>${type === 'success' ? '✅' : '❌'}</span>
                        <span>${message}</span>
                    `;

                    document.body.appendChild(toast);

                    // 显示动画
                    setTimeout(() => toast.classList.add('show'), 100);

                    // 3秒后自动消失
                    setTimeout(() => {
                        toast.classList.remove('show');
                        setTimeout(() => toast.remove(), 300);
                    }, 3000);
                }

                // 文件拖拽功能
                fileLabel.addEventListener('dragover', function(e) {
                    e.preventDefault();
                    fileLabel.style.borderColor = '#4f46e5';
                    fileLabel.style.background = 'linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%)';
                });

                fileLabel.addEventListener('dragleave', function(e) {
                    e.preventDefault();
                    fileLabel.style.borderColor = '#d1d5db';
                    fileLabel.style.background = 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)';
                });

                fileLabel.addEventListener('drop', function(e) {
                    e.preventDefault();
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        imageFileInput.files = files;
                        updateFileLabel(files[0]);
                    }
                    fileLabel.style.borderColor = '#d1d5db';
                    fileLabel.style.background = 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)';
                });

                // 文件选择更新
                imageFileInput.addEventListener('change', function(e) {
                    if (e.target.files.length > 0) {
                        updateFileLabel(e.target.files[0]);
                    }
                    errorDiv.style.display = 'none';
                });

                function updateFileLabel(file) {
                    fileLabelText.textContent = `已选择: ${file.name}`;
                    fileLabel.classList.add('has-file');
                }

                // 图像点击放大功能
                visualizationImage.addEventListener('click', function() {
                    modalImage.src = visualizationImage.src;
                    imageModal.style.display = 'block';
                    document.body.style.overflow = 'hidden';
                });

                // 关闭模态框
                closeModal.addEventListener('click', function() {
                    imageModal.style.display = 'none';
                    document.body.style.overflow = 'auto';
                });

                // 点击模态框背景关闭
                imageModal.addEventListener('click', function(e) {
                    if (e.target === imageModal) {
                        imageModal.style.display = 'none';
                        document.body.style.overflow = 'auto';
                    }
                });

                // ESC键关闭模态框
                document.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape' && imageModal.style.display === 'block') {
                        imageModal.style.display = 'none';
                        document.body.style.overflow = 'auto';
                    }
                });

                // 检查服务器健康状态
                fetch(`${API_BASE_URL}/health`)
                    .then(response => response.json())
                    .then(data => {
                        console.log('服务器状态:', data);
                        enhancementAvailable = data.enhancement_available;

                        if (!enhancementAvailable) {
                            useEnhancementCheckbox.disabled = true;
                            enhancementItem.classList.add('disabled');
                            enhancementWarning.style.display = 'block';
                        }
                    })
                    .catch(error => {
                        errorDiv.textContent = '无法连接到服务器，请确保服务器已启动。';
                        errorDiv.style.display = 'block';
                        processBtn.disabled = true;
                    });

                // 处理选项变化时更新加载提示
                function updateLoadingSteps() {
                    const steps = [];
                    if (useEnhancementCheckbox.checked && enhancementAvailable) {
                        steps.push('外观增强');
                    }
                    if (useDewarpCheckbox.checked) {
                        steps.push('扭曲矫正');
                    }
                    steps.push('Combo OCR识别');

                    loadingSteps.textContent = '图像处理步骤：' + steps.join(' → ');
                }

                useEnhancementCheckbox.addEventListener('change', updateLoadingSteps);
                useDewarpCheckbox.addEventListener('change', updateLoadingSteps);
                updateLoadingSteps();

                processBtn.addEventListener('click', function() {
                    const file = imageFileInput.files[0];
                    if (!file) {
                        showError('请先选择图片');
                        return;
                    }

                    // 检查文件格式
                    const validExtensions = ['.png', '.jpg', '.jpeg', '.bmp'];
                    const fileName = file.name.toLowerCase();
                    const isValidFile = validExtensions.some(ext => fileName.endsWith(ext));

                    if (!isValidFile) {
                        showError(`不支持的文件格式。支持的格式: ${validExtensions.join(', ')}`);
                        return;
                    }

                    // 隐藏之前的结果和错误
                    resultsDiv.style.display = 'none';
                    errorDiv.style.display = 'none';

                    // 显示加载指示器
                    loadingDiv.style.display = 'block';
                    loadingDiv.classList.add('fade-in');
                    updateLoadingSteps();

                    // 禁用按钮
                    processBtn.disabled = true;

                    // 创建FormData对象
                    const formData = new FormData();
                    formData.append('image', file);
                    formData.append('use_enhancement', useEnhancementCheckbox.checked);
                    formData.append('use_dewarp', useDewarpCheckbox.checked);

                    // 发送请求
                    fetch(`${API_BASE_URL}/process`, {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('服务器响应错误: ' + response.status);
                        }
                        return response.json();
                    })
                    .then(data => {
                        // 隐藏加载指示器
                        loadingDiv.style.display = 'none';

                        // 启用按钮
                        processBtn.disabled = false;

                        if (data.error) {
                            showError(data.error);
                            return;
                        }

                        // 显示排序后的文本结果到可编辑文本区域
                        textResultTextarea.value = data.sorted_text || '未识别到文本';

                        // 显示处理信息
                        if (data.processing_info) {
                            const info = data.processing_info;
                            processingInfoDiv.innerHTML = `
                                <strong>处理信息:</strong><br>
                                外观增强: ${info.use_enhancement ? '✅ 已启用' : '⏭️ 已跳过'}<br>
                                扭曲矫正: ${info.use_dewarp ? '✅ 已启用' : '⏭️ 已跳过'}<br>
                                检测到文本区域: ${info.text_regions_count} 个
                            `;
                        }

                        // 显示可视化图像
                        if (data.visualization) {
                            visualizationImage.src = 'data:image/png;base64,' + data.visualization;
                            visualizationImage.style.display = 'block';
                            visualizationImage.classList.add('fade-in');
                        }

                        // 显示结果区域
                        resultsDiv.style.display = 'block';
                        resultsDiv.classList.add('slide-up');

                        // 平滑滚动到结果
                        setTimeout(() => {
                            resultsDiv.scrollIntoView({ behavior: 'smooth' });
                        }, 100);

                        // 显示成功提示
                        if (data.sorted_text && data.sorted_text.trim()) {
                            showToast('OCR识别完成！');
                        }
                    })
                    .catch(error => {
                        // 隐藏加载指示器
                        loadingDiv.style.display = 'none';

                        // 启用按钮
                        processBtn.disabled = false;

                        showError('请求错误: ' + error.message);
                    });
                });

                function showError(message) {
                    errorDiv.textContent = message;
                    errorDiv.style.display = 'block';
                    errorDiv.classList.add('fade-in');
                    errorDiv.scrollIntoView({ behavior: 'smooth' });
                }
            });