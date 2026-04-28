import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import matplotlib.patches as patches
import json
import os
from matplotlib.widgets import Button, Slider, TextBox
import matplotlib as mpl

# 設置中文字體顯示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Heiti TC', 'sans-serif'] 
plt.rcParams['axes.unicode_minus'] = False  # 正確顯示負號

class PointSelector:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = np.array(Image.open(image_path))
        self.points = []  # 儲存選取的點 [(x, y), ...]
        self.markers = []  # 儲存標記物件
        self.point_values = []  # 儲存每個點的數值
        self.sliders = []  # 儲存每個點的滑桿
        self.min_value = 0  # 最小值
        self.max_value = 1  # 最大值，適合深度圖的0-1範圍
        
        # 創建圖形和軸 - 使用GridSpec更好地控制布局
        self.fig = plt.figure(figsize=(16, 8))
        gs = self.fig.add_gridspec(1, 2, width_ratios=[1, 1])
        
        # 左側放圖片
        self.ax = self.fig.add_subplot(gs[0, 0])
        
        # 右側區域用於滑桿和標籤
        self.controls_area = self.fig.add_subplot(gs[0, 1])
        self.controls_area.set_title('點數值調整')
        
        # 完全隱藏右側區域的所有軸線
        self.controls_area.spines['right'].set_visible(False)
        self.controls_area.spines['top'].set_visible(False)
        self.controls_area.spines['left'].set_visible(False)
        self.controls_area.spines['bottom'].set_visible(False)
        self.controls_area.set_xticks([])
        self.controls_area.set_yticks([])
        
        # 設置控制區域的座標範圍
        self.controls_area.set_xlim(0, 1)
        self.controls_area.set_ylim(0, 1)
        
        # 顯示圖片
        self.ax.imshow(self.image)
        self.ax.set_title('點擊圖片以選擇位置 (按 s 儲存)')
        
        # 添加按鈕 - 移至整個視窗的左上角
        btn_width = 0.06
        btn_height = 0.05
        btn_spacing = 0.01
        
        # 計算按鈕在figure中的位置（整個視窗的左上角）
        save_x = 0.01
        clear_x = save_x + btn_width + btn_spacing
        undo_x = clear_x + btn_width + btn_spacing
        btn_y = 0.94  # 接近頂部
        
        self.ax_save = plt.axes([save_x, btn_y, btn_width, btn_height])
        self.ax_clear = plt.axes([clear_x, btn_y, btn_width, btn_height])
        self.ax_undo = plt.axes([undo_x, btn_y, btn_width, btn_height])
        
        self.btn_save = Button(self.ax_save, '儲存')
        self.btn_clear = Button(self.ax_clear, '清除')
        self.btn_undo = Button(self.ax_undo, '復原')
        
        self.btn_save.on_clicked(self.save_points)
        self.btn_clear.on_clicked(self.clear_points)
        self.btn_undo.on_clicked(self.undo_point)
        
        # 添加最大最小值設置
        self.ax_min_label = plt.axes([0.7, 0.05, 0.05, 0.04])
        self.ax_min_label.text(0.5, 0.5, '最小值:', ha='center', va='center')
        self.ax_min_label.axis('off')
        
        self.ax_min = plt.axes([0.75, 0.05, 0.05, 0.04])
        self.txt_min = TextBox(self.ax_min, '', initial='0')
        self.txt_min.on_submit(self.update_min_value)
        
        self.ax_max_label = plt.axes([0.85, 0.05, 0.05, 0.04])
        self.ax_max_label.text(0.5, 0.5, '最大值:', ha='center', va='center')
        self.ax_max_label.axis('off')
        
        self.ax_max = plt.axes([0.9, 0.05, 0.05, 0.04])
        self.txt_max = TextBox(self.ax_max, '', initial='1')
        self.txt_max.on_submit(self.update_max_value)
        
        # 連接點擊事件
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.kid = self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        
        # 初始化滑桿顯示區域
        self.update_sliders()

    def update_min_value(self, text):
        try:
            self.min_value = float(text)
            self.update_sliders_range()
        except ValueError:
            print("請輸入有效的數字")
    
    def update_max_value(self, text):
        try:
            self.max_value = float(text)
            self.update_sliders_range()
        except ValueError:
            print("請輸入有效的數字")
    
    def update_sliders_range(self):
        # 更新所有滑桿的範圍
        if self.min_value >= self.max_value:
            print("最小值必須小於最大值")
            return
        
        self.controls_area.set_xlim(self.min_value, self.max_value)
        
        # 重新創建所有滑桿
        self.update_sliders()
        
        self.fig.canvas.draw()
    
    def update_sliders(self):
        # 清除現有的滑桿
        for slider in self.sliders:
            slider.ax.remove()
        self.sliders = []
        
        # 清除右側區域
        self.controls_area.clear()
        self.controls_area.set_title('點數值調整')
        
        # 隱藏所有軸線和刻度
        self.controls_area.set_xticks([])
        self.controls_area.set_yticks([])
        self.controls_area.spines['right'].set_visible(False)
        self.controls_area.spines['top'].set_visible(False)
        self.controls_area.spines['left'].set_visible(False)
        self.controls_area.spines['bottom'].set_visible(False)
        
        # 設置控制區域的座標範圍
        self.controls_area.set_xlim(0, 1)
        self.controls_area.set_ylim(0, 1)
        
        # 獲取controls_area在圖表中的位置和大小
        bbox = self.controls_area.get_position()
        controls_x = bbox.x0
        controls_y = bbox.y0
        controls_width = bbox.width
        controls_height = bbox.height
        
        # 確保點值列表與點的數量一致
        while len(self.point_values) < len(self.points):
            self.point_values.append(0.5 * (self.min_value + self.max_value))  # 默認值為範圍中間值
        
        # 如果沒有點，則顯示提示訊息
        if len(self.points) == 0:
            self.controls_area.text(0.5, 0.5, '在左側圖片上點擊以添加點', 
                                    ha='center', va='center', transform=self.controls_area.transAxes)
            self.fig.canvas.draw()
            return
        
        # 計算顯示的點數量（限制最多顯示點的數量）
        num_points_to_show = min(len(self.points), 20)
        
        # 計算每個滑桿的垂直位置（從上到下均勻分布）
        y_positions = np.linspace(0.9, 0.15, num_points_to_show)
        
        # 滑桿參數 - 調整為controls_area內的相對位置
        slider_left = 0.35  # 滑桿左邊緣位置 (相對於controls_area)
        slider_width = 0.4  # 滑桿寬度
        slider_height = 0.02  # 滑桿高度 (相對於controls_area)
        
        # 在右側顯示數值範圍
        self.controls_area.text(0.5, 0.05, f'最小值: {self.min_value}     最大值: {self.max_value}', 
                             ha='center', va='center', transform=self.controls_area.transAxes)
        
        # 為每個點創建標籤和滑桿
        for i, (x, y) in enumerate(self.points):
            if i >= num_points_to_show:  # 超過顯示限制
                break
                
            # 當前點的垂直位置
            y_pos = y_positions[i]
            
            # 創建點的標籤文字 (放在滑桿左側)
            label = f'點 {i+1} ({x},{y})'
            self.controls_area.text(slider_left - 0.05, y_pos, label, 
                                    ha='right', va='center', 
                                    transform=self.controls_area.transAxes)
            
            # 計算滑桿在figure中的實際位置
            slider_fig_left = controls_x + slider_left * controls_width
            slider_fig_bottom = controls_y + (y_pos - slider_height/2) * controls_height
            slider_fig_width = slider_width * controls_width
            slider_fig_height = slider_height * controls_height
            
            # 創建滑桿（使用figure座標系）
            ax_slider = self.fig.add_axes([slider_fig_left, slider_fig_bottom, 
                                          slider_fig_width, slider_fig_height])
            
            # 創建滑桿
            slider = Slider(
                ax_slider, '', 
                self.min_value, self.max_value, 
                valinit=self.point_values[i]
            )
            
            # 自定義滑桿外觀
            slider.valtext.set_visible(False)  # 隱藏滑桿自帶的數值顯示
            
            # 創建數值顯示（滑桿右側）
            value_text = self.controls_area.text(slider_left + slider_width + 0.02, y_pos, f'{self.point_values[i]:.3f}', 
                                                ha='left', va='center',
                                                transform=self.controls_area.transAxes,
                                                fontsize=10, fontweight='bold',
                                                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7))
            
            # 設置滑桿更新函數
            def update_value(val, idx=i, text=value_text):
                self.point_values[idx] = val
                text.set_text(f'{val:.3f}')
                self.fig.canvas.draw_idle()
            
            slider.on_changed(update_value)
            self.sliders.append(slider)
        
        # 調整圖表布局
        self.fig.tight_layout(pad=3.0)
        
        self.fig.canvas.draw()

    def on_click(self, event):
        # 確保點擊在圖片範圍內
        if event.inaxes != self.ax:
            return
        
        x, y = int(event.xdata), int(event.ydata)
        self.points.append((x, y))
        
        # 從深度圖中獲取該位置的實際數值作為預設值
        if 0 <= y < self.image.shape[0] and 0 <= x < self.image.shape[1]:
            # 如果是彩色圖像，取平均值或使用第一個通道
            if len(self.image.shape) == 3:
                pixel_value = self.image[y, x].mean()  # 取RGB平均值
            else:
                pixel_value = self.image[y, x]  # 灰度圖
            
            # 將像素值歸一化到0-1範圍（假設原始像素值為0-255）
            if pixel_value > 1.0:  # 如果像素值大於1，說明是0-255範圍
                default_value = pixel_value / 255.0
            else:  # 如果像素值小於等於1，說明已經是0-1範圍
                default_value = float(pixel_value)
            
            # 確保數值在設定的範圍內
            default_value = max(self.min_value, min(self.max_value, default_value))
        else:
            # 如果點擊位置超出圖片範圍，使用範圍中間值
            default_value = 0.5 * (self.min_value + self.max_value)
        
        self.point_values.append(default_value)
        
        # 繪製高亮標記 (紅色圓圈)
        circle = patches.Circle((x, y), radius=5, color='red', alpha=1)
        self.ax.add_patch(circle)
        self.markers.append(circle)
        
        # 顯示座標、索引和數值
        current_value = self.point_values[-1]  # 獲取剛添加的點的數值
        text = self.ax.text(x+15, y, f'點 {len(self.points)}: ({x},{y})\n深度: {current_value:.3f}', color='white', 
                            bbox=dict(facecolor='red', alpha=0.7))
        self.markers.append(text)
        
        # 更新標題顯示點數
        self.ax.set_title(f'已選擇 {len(self.points)} 個點 (按 s 儲存)')
        
        # 更新滑桿
        self.update_sliders()
        
    def on_key(self, event):
        if event.key == 's':
            self.save_points(event)
    
    def save_points(self, event):
        # 生成文件名 (使用原圖檔名加上_points.json)
        base_name = os.path.splitext(os.path.basename(self.image_path))[0]
        output_file = f"{base_name}_points.json"
        
        # 創建包含座標和數值的完整數據
        point_data = []
        for i, (x, y) in enumerate(self.points):
            value = self.point_values[i] if i < len(self.point_values) else 0.5
            point_data.append({
                'position': (x, y),
                'value': float(value)
            })
        
        # 儲存點座標和數值到JSON檔案
        with open(output_file, 'w') as f:
            json.dump(point_data, f)
        
        # 創建與圖片相同size的零矩陣
        mask = np.zeros(self.image.shape[:2], dtype=np.float32)
        
        # 將選取的點座標設為對應滑桿的數值
        for i, (x, y) in enumerate(self.points):
            if 0 <= y < mask.shape[0] and 0 <= x < mask.shape[1]:
                value = self.point_values[i] if i < len(self.point_values) else 0.5
                mask[y, x] = value
                
        # 儲存矩陣
        mask_file = f"{base_name}_mask.npy"
        np.save(mask_file, mask)
        
        print(f"點座標和數值已儲存至 {output_file}")
        print(f"遮罩矩陣已儲存至 {mask_file}")
        print("儲存的點詳細資訊:")
        for i, ((x, y), val) in enumerate(zip(self.points, self.point_values)):
            print(f"  點 {i+1}: 座標=({x}, {y}), 深度值={val:.3f}")
        self.ax.set_title(f'已儲存 {len(self.points)} 個點和遮罩矩陣')
        self.fig.canvas.draw()
    
    def clear_points(self, event):
        # 清除所有選取的點
        self.points = []
        self.point_values = []
        
        # 移除所有標記
        for marker in self.markers:
            marker.remove()
        self.markers = []
        
        # 重設標題
        self.ax.set_title('點擊圖片以選擇位置 (按 s 儲存)')
        
        # 更新滑桿
        self.update_sliders()
        
        self.fig.canvas.draw()
    
    def undo_point(self, event):
        # 移除最後一個點
        if self.points:
            self.points.pop()
            if self.point_values:
                self.point_values.pop()
            
            # 移除最後兩個標記 (圓圈和文字)
            if self.markers:
                self.markers.pop().remove()  # 移除文字
            if self.markers:
                self.markers.pop().remove()  # 移除圓圈
            
            # 更新標題
            self.ax.set_title(f'已選擇 {len(self.points)} 個點 (按 s 儲存)')
            
            # 更新滑桿
            self.update_sliders()
            
            self.fig.canvas.draw()

    def run(self):
        plt.show()


if __name__ == "__main__":
    # 設置圖片路徑
    image_path = 'ComfyUI_temp_sgucl_00002_.png'  # 更改為你的圖片路徑
    
    # 創建並運行點選器
    selector = PointSelector(image_path)
    selector.run()
    
    # 程式結束時顯示選取的點
    print("選取的點座標和深度值:")
    for i, ((x, y), val) in enumerate(zip(selector.points, selector.point_values)):
        print(f"點 {i+1}: 座標=({x}, {y}), 深度值={val:.3f}") 