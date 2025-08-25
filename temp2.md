现在要编写功能模块的开发文档，现在由于项目已经编写了两个月了，已经实现了很多 API 接口功能，现在开发文档要补全这个
对于这部分，首先我的 api 路由进行了分组，有基础模块路由和路径路由这两个子路由，这两个子路由又进行了分组，至少在基础模块路由这里，除了 paths 表的，其他基础的 CRUD 都是通用的，所以我觉得这个的功能模块可以介绍那个通用的CRUD 功能模块，以一个代表所有的基础功能，然后就是 paths 表的功能模块，后面就是用户路径 user_paths，再到检测记录然后再到最后的评分，总之一个一个来吧。然后编写这个功能模块的开发文档，主要是介绍功能和 utils 文件夹里面的工具函数，讲解功能的定义和实现，每个业务逻辑场景是怎么做的。比如下面是一个介绍 ocr 功能的写法，当然不是完全全部用下面的写法，有一些是可以减少的，基本上要保留的是对这个功能的介绍，是干什么的，然后还要声明这个功能在哪里实现的，算是一个定位吧，涉及到了什么文件，从文件夹到文件的一个链路，当然指出关键文件就是，不是全部文件都需要指出来，然后还要介绍它的辅助函数，像下面那样简单的概述一下辅助函数的功能就可以了，基本上可以说完后就能够清晰的知道这个功能是怎么实现的，怎么定义的，怎么思考的

# 4.3. OCR

这里介绍 OCR （光学字符识别）。

Alas 使用了 [cnocr](https://github.com/breezedeus/cnocr) 作为 OCR 库，也针对碧蓝航线内的字体训练了两个 OCR 模型。许多脚本都迈不过 OCR 这道坎，需要依赖在线 OCR，但是在 Alas 里，你可以大量地调用 OCR。

需要注意的是 OCR 是无法达到 100% 正确率的，在调用时需要注意异常处理。

## 预训练模型

Alas 里有 3 个 OCR 模型：

- cnocr  是 cnocr 的默认模型，支持中英文

```

# Folder: ./bin/cnocr_models/cnocr

# Size: 9.51MB

# Model: densenet-lite-gru

# Epoch: 39

# Validation accuracy: 99.04%

# Font: Various

# Charset: Number, English character, Chinese character, symbols, <space>

# numclasses: 6426

```

- azur_lane 针对碧蓝航线数字和字母，仿照 cnocr 默认模型训练

```

# Folder: ./bin/cnocr_models/azur_lane

# Size: 3.25MB

# Model: densenet-lite-gru

# Epoch: 15

# Validation accuracy: 99.43%

# Font: Impact, AgencyFB-Regular, MStiffHeiHK-UltraBold

# Charset: 0123456789ABCDEFGHIJKLMNPQRSTUVWXYZ:/- (Letter 'O' and <space> is not included)

# numclasses: 39

```

- jp 针对日文，同样仿照 cnocr 默认模型训练

```

具体信息忘了（逃

```

## 对 cnocr 的修改

Alas 对 cnocr 进行了简单的修改，`module/ocr/al_ocr.py` 覆写了一些 cnocr 的方法：

1. _assert_and_prepare_model_files

   取消了自动下载默认模型

2. _preprocess_img_array

   图片预处理改成纯 opencv 实现，提高速度

3. init

   模型懒加载

4. _gen_line_pred_chars

   去除了准确率在 0.5 以下的字符输出

5. debug

   增加了一个展示预处理后的图片的方法

## Ocr

通用的 OCR 类

以关卡名称 OCR 为例：

```python

# 创建 Ocr 对象

# 可以是个 button，也可以是一个 list 的 button

ocr = Ocr(buttons, name='campaign', letter=(255, 255, 255), threshold=128,

          alphabet='0123456789ABCDEFGHIJKLMNPQRSTUVWXYZ-')

# 获取识别结果

result = ocr.ocr(image)

```

## Digit

识别数字。返回 int

如果识别结果不能转换为 int，返回 0。

## DigitCounter

识别数字计数，例如  14/15，返回 (14, 1, 15)。

如果识别结果不符合 {x}/{y} 的格式，返回 (0, 0, 0)。

## Duration

识别时长，例如 08:00:00，返回 datetime.timedelta 对象。

如果识别结果不符合 {h}:{m}:{s} 的格式，返回时长为 0 的 datetime.timedelta 对象。