def select_layers(layers: str):
    return f'''\
(defun c:runplot ( / layers idx layname ss)
  ;; список слоёв, которыми управляем
  (setq layers '({layers}))

  ;; если глобальная переменная не существует — создаём
  (if (not *layerIndex*)
    (setq *layerIndex* 0)
  )

  ;; если первый запуск (index = 0), то скрыть все слои
  (if (= *layerIndex* 0)
    (progn
      (foreach lay layers
        (if (tblsearch "LAYER" lay)
          (command "_.LAYER" "_OFF" lay "")
        )
      )
      (princ "\\nВсе слои из списка скрыты.")
    )
    ;; иначе делаем видимым соответствующий слой и выделяем объекты
    (progn
      (setq idx (1- *layerIndex*))
      (if (< idx (length layers))
        (progn
          (setq layname (nth idx layers))
          (if (tblsearch "LAYER" layname)
            (progn
              ;; включаем слой
              (command "_.LAYER" "_ON" layname "")

              ;; выбираем все объекты на этом слое
              (setq ss (ssget "X" (list (cons 8 layname))))
              (if ss
                (progn
                  (sssetfirst nil ss) ;; выделение объектов
                  (princ (strcat "\\nСлой включён и объекты выбраны: " layname))
                )
                (princ (strcat "\\nСлой включён, но объектов нет: " layname))
              )
            )
          )
        )
      )
    )
  )

  ;; увеличить индекс
  (setq *layerIndex* (1+ *layerIndex*))

  ;; если вышли за пределы списка, сбросить
  (if (> *layerIndex* (length layers))
    (setq *layerIndex* 0)
  )

  (princ)
)
'''

def set_layer(type_element):
    return f'''\
;; "{type_element}"
(defun SetLayer (layername color lineweight)
  ;; Проверить существование слоя
  (if (not (tblsearch "LAYER" layername))
    ;; Создать слой
    (command "_-LAYER"
             "_M" layername      ; Создать слой
             "_C" color ""       ; Задать цвет
             "_LW" lineweight "" ; Задать вес линии
             ""                  ; Закрыть команду
    )
  )

  ;; Переключиться на слой
  (setvar "CLAYER" layername)
)
'''

def create_autocad_block_device():
    return f'''\
(defun CreateBlockWithVertices (blkName Layer width height vertexList / pt0 pt1 pt2 pt3)
  ;; Удаляем существующий блок
  (if (tblsearch "BLOCK" blkName)
    (command "_.-PURGE" "_B" blkName "_N")
  )

  ;; Начинаем определение блока
  (entmake (list (cons 0 "BLOCK")
                 (cons 2 blkName)
                 (cons 70 0)
                 (cons 10 '(0.0 0.0 0.0))
           )
  )

  ;; Рисуем прямоугольник (замкнутая LWPOLYLINE)
  (setq pt1 '(0.0 0.0)
        pt2 (list width 0.0)
        pt3 (list width height)
        pt4 (list 0.0 height)
  )
  (entmake (list '(0 . "LINE") (cons 8 Layer) (cons 10 pt1) (cons 11 pt2)))
  (entmake (list '(0 . "LINE") (cons 8 Layer) (cons 10 pt2) (cons 11 pt3)))
  (entmake (list '(0 . "LINE") (cons 8 Layer) (cons 10 pt3) (cons 11 pt4)))
  (entmake (list '(0 . "LINE") (cons 8 Layer) (cons 10 pt4) (cons 11 pt1)))
  (entmake (list (cons 0 "LWPOLYLINE")
	         (cons 100 "AcDbEntity")
			 (cons 8 "0")
	         (cons 100 "AcDbPolyline")
	         (cons 90 4)
	         (cons 70 1)
	         (cons 10 pt1)
	         (cons 10 pt2)
	         (cons 10 pt3)
	         (cons 10 pt4)	
	       )
  )

  ;; Добавляем текстовые метки
  (foreach v vertexList
	(entmake (list (cons 0 "TEXT")
               (cons 8 Layer)
               (cons 10 (list (cadr v) (caddr v)))
               (cons 11 (list (cadr v) (caddr v)))
               (cons 40 2.0)
               (cons 1 (car v))
               (cons 72 1) ; горизонтальное выравнивание: центр
               (cons 73 2) ; вертикальное выравнивание: по центру
			 )
	)
    (entmake (list (cons 0 "CIRCLE") (cons 8 "0") (cons 10 (list (cadr v) (caddr v))) (cons 40 3)))
  )

  ;; Завершаем определение блока
  (entmake (list (cons 0 "ENDBLK")))

  ;; Возвращаем имя блока
  blkName
)
'''

def insert_device_with_contacts(lisp_code):
    return f'''\
(defun c:runplot (/)
  (vl-load-com)
{lisp_code}
  (princ)
)

;; Утилита: найти атрибут по тегу
(defun find-attribute (attlist tag / att-found)
  (foreach att attlist
    (if (= (strcase (vla-get-TagString att))
           (strcase tag))
      (setq att-found att)
    )
  )
  att-found
)

;; Утилита: найти динамическое свойство по имени
(defun find-dynprop (proplist name / prop-found)
  (foreach prop proplist
    (if (= (strcase (vla-get-PropertyName prop))
           (strcase name))
      (setq prop-found prop)
    )
  )
  prop-found
)


(defun make_variant_float (value)
  (vlax-make-variant value 5)
)

(defun make_variant_string (value)
  (vlax-make-variant value 8)
)

;; Оптимизированная вставка БЛОКа
(defun InsertBlock (point x y info count name_device row man art type / blockObj atts props)
  (setq blockObj
    (vla-InsertBlock
      (vla-get-ModelSpace (vla-get-ActiveDocument (vlax-get-acad-object)))
      (vlax-3d-point point)
      "БЛОК"
      1.0 1.0 1.0 0.0
    )
  )

  (setq atts (vlax-safearray->list (vlax-variant-value (vla-GetAttributes blockObj))))
  (setq props (vlax-safearray->list (vlax-variant-value (vla-GetDynamicBlockProperties blockObj))))

  ;; Изменение атрибутов
  (if (setq att (find-attribute atts "ИНФОРМАЦИЯ"))   (vla-put-TextString att info))
  (if (setq att (find-attribute atts "КОЛИЧЕСТВО"))   (vla-put-TextString att count))
  (if (setq att (find-attribute atts "ИМЯ"))          (vla-put-TextString att name_device))
  (if (setq att (find-attribute atts "РЯД"))          (vla-put-TextString att row))
  (if (setq att (find-attribute atts "ПРОИЗВОДИТЕЛЬ"))(vla-put-TextString att man))
  (if (setq att (find-attribute atts "АРТИКУЛ"))      (vla-put-TextString att art))
  (if (setq att (find-attribute atts "ТИП"))          (vla-put-TextString att type))

  ;; Изменение динамических свойств
  (if (setq prop (find-dynprop props "Ширина"))
    (vla-put-Value prop (make_variant_float x))
  )
  (if (setq prop (find-dynprop props "Высота"))
    (vla-put-Value prop (make_variant_float y))
  )
  (if (setq prop (find-dynprop props "Видимость информации"))
    (vla-put-Value prop (make_variant_string "Скрыто"))
  )
  blockObj
)

;; Аналогично для КОНТАКТ
(defun InsertContact (point name_device number direction type x y / blockObj atts props)
  (setq blockObj
    (vla-InsertBlock
      (vla-get-ModelSpace (vla-get-ActiveDocument (vlax-get-acad-object)))
      (vlax-3d-point point)
      "КОНТАКТ"
      1.0 1.0 1.0 0.0
    )
  )

  (setq atts (vlax-safearray->list (vlax-variant-value (vla-GetAttributes blockObj))))
  (setq props (vlax-safearray->list (vlax-variant-value (vla-GetDynamicBlockProperties blockObj))))

  (if (setq att (find-attribute atts "ИМЯ"))       (vla-put-TextString att name_device))
  (if (setq att (find-attribute atts "НОМЕР"))     (vla-put-TextString att number))
  (if (setq att (find-attribute atts "МОНТАЖ"))    (vla-put-TextString att direction))
  (if (setq att (find-attribute atts "ТИП"))       (vla-put-TextString att type))

  (if (setq prop (find-dynprop props "Положение1 X"))
    (vla-put-Value prop (make_variant_float x))
  )
  (if (setq prop (find-dynprop props "Положение1 Y"))
    (vla-put-Value prop (make_variant_float y))
  )
  blockObj
) 
'''

def get_style_width(type_element):
    return f'''\
;; "{type_element}"
(defun get-style-width (name)
  (if (setq tbl (tblsearch "STYLE" name))
    (if (setq p (assoc 41 tbl)) (cdr p) 1.0)
    1.0
  )
)
'''