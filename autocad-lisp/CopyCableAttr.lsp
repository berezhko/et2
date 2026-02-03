(defun c:CopyCableAttr ( / blockRef cableValue entData entType )

  ;; Функция для получения значения атрибута по тегу из ВСТАВКИ блока
  ;; Использует подход из рабочей программы CreateWire
  (defun get-attr-value-from-blockref (blkref_ent tag / vla_blk_obj attrib_list attr_vla_obj attr_val)
    ;; Получаем VLA-объект вставленного блока
    (setq vla_blk_obj (vlax-ename->vla-object blkref_ent))
    ;; Получаем список атрибутов, присоединённых к этой вставке через VLA
    ;; Используем тот же подход, что и в CreateWire
    (setq attrib_list (vlax-safearray->list
                         (vlax-variant-value (vla-GetAttributes vla_blk_obj))
                       )
    )
    ;; Проходим по списку VLA-объектов атрибутов
    (foreach attr_vla_obj attrib_list
      ;; Проверяем тег атрибута через VLA-свойство TagString
      (if (and (not attr_val) (equal (vla-get-TagString attr_vla_obj) tag)) ; Проверяем, что значение ещё не найдено
        ;; Если тег совпал и значение ещё не установлено, получаем значение через VLA-свойство TextString
        (setq attr_val (vla-get-TextString attr_vla_obj))
      )
    )
    ;; Возвращаем значение или nil, если атрибут не найден
    attr_val
  )

  ;; Функция для установки значения атрибута по тегу в ВСТАВКЕ блока
  ;; Использует подход из рабочей программы CreateWire
  (defun set-attr-value-in-blockref (blkref_ent tag new_value / vla_blk_obj attrib_list attr_vla_obj found)
    ;; Получаем VLA-объект вставленного блока
    (setq vla_blk_obj (vlax-ename->vla-object blkref_ent))
    ;; Получаем список атрибутов
    (setq attrib_list (vlax-safearray->list
                         (vlax-variant-value (vla-GetAttributes vla_blk_obj))
                       )
    )
    ;; Проходим по списку VLA-объектов атрибутов
    (foreach attr_vla_obj attrib_list
      ;; Проверяем тег
      (if (equal (vla-get-TagString attr_vla_obj) tag)
        (progn
          ;; Устанавливаем новое значение через VLA-свойство TextString
          (vla-put-TextString attr_vla_obj (strcat new_value)) ; Приведение к строке на всякий случай
          (entupd blkref_ent) ; Обновляем отображение блока
          (setq found T) ; Помечаем, что нашли и изменили
        )
      )
    )
    found ; Возвращаем T, если атрибут был найден и изменён, иначе nil
  )

  ;; Основной код
  ;; Загружаем VLA функции, как в CreateWire
  (vl-load-com)

  (princ "\nВыберите блок КАБЕЛЬ3: ")
  (setq blockRef (entsel))
  (if blockRef
    (progn
      (setq blockRef (car blockRef))
      ;; Проверяем, что выбрана сущность INSERT и её имя блока "КАБЕЛЬ3"
      (setq entData (entget blockRef))
      ;; Используем VLA для проверки имени
      (setq vla_obj_source (vlax-ename->vla-object blockRef))
      (if (and entData
               (equal (cdr (assoc 0 entData)) "INSERT") ; Убедимся, что это вставка блока
               (wcmatch (vla-get-EffectiveName vla_obj_source) "КАБЕЛЬ3")) ; Проверка имени блока через EffectiveName
        (progn
          (setq cableValue (get-attr-value-from-blockref blockRef "КАБЕЛЬ"))
          (if cableValue
            (progn
              (princ (strcat "\nЗначение атрибута КАБЕЛЬ: " cableValue))
              (while (progn
                       (princ "\nВыберите блок КЛЕММА1 или КЛЕММА2 (Esc для выхода): ")
                       (setq blockRef (entsel))
                       (if blockRef
                         (progn
                           (setq blockRef (car blockRef))
                           (setq entData (entget blockRef))
                           ;; Проверяем, что это вставка блока
                           (if (and entData
                                    (equal (cdr (assoc 0 entData)) "INSERT"))
                             (progn
                               ;; Получаем VLA-объект целевого блока
                               (setq vla_obj_target (vlax-ename->vla-object blockRef))
                               ;; Проверяем имя блока через EffectiveName
                               (setq effective_name (vla-get-EffectiveName vla_obj_target))
                               (if (wcmatch effective_name "КЛЕММА1,КЛЕММА2")
                                 (progn
                                   ;; Попробуем выполнить установку и посмотреть результат
                                   (if (set-attr-value-in-blockref blockRef "КАБЕЛЬ" cableValue)
                                     (princ "\nАтрибут КАБЕЛЬ обновлён.")
                                     (princ (strcat "\nАтрибут КАБЕЛЬ в целевом блоке не найден. EffectiveName: " effective_name))
                                   )
                                 )
                                 (princ (strcat "\nНеверный тип блока: " effective_name ". Ожидается КЛЕММА1 или КЛЕММА2."))
                               )
                             )
                             (princ "\nВыбранный объект не является вставкой блока.")
                           )
                         )
                         ;; Если entsel вернул nil, значит Esc
                         (exit nil)
                       )
                     )
              )
            )
            (princ "\nАтрибут КАБЕЛЬ в блоке КАБЕЛЬ3 не найден или пуст.")
          )
        )
        (princ "\nВыбранный объект не является блоком КАБЕЛЬ3.")
      )
    )
    (princ "\nБлок не выбран.")
  )
  (princ)
)