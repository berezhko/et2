(defun c:CreateRef (/ obj vla_obj V po bl_name osm)  
  (vl-load-com) ; загружаем функции расширения
    (setq obj (car (entsel "\nВыберите блок: ")))
    (if (not (= obj nil))
      (progn
        (setq vla_obj (vlax-ename->vla-object obj)) ; переводим в vla-object
        (setq lst (vlax-safearray->list
          (vlax-variant-value (vla-GetAttributes vla_obj)))
        )

        (foreach item lst
			(if (= (vla-get-TagString item) "ИНФОРМАЦИЯ")  (setq info (vla-get-TextString item)))
			(if (= (vla-get-TagString item) "ПРОИЗВОДИТЕЛЬ")  (setq manuf (vla-get-TextString item)))
			(if (= (vla-get-TagString item) "АРТИКУЛ")  (setq art (vla-get-TextString item)))

	)
	;(setq reference (strcat manuf ":" art))
	(setq reference "00")
      );end progn
    ); end ifz

    (setq po (getpoint "\nУкажите базовую точку : "))        ; запрос координат базовой точки
    (command "_insert" "ВЫНОСКА" po 1 1 0)  ; вставка блока
	
    (setq lst (vlax-safearray->list
        (vlax-variant-value (vla-GetAttributes (vlax-ename->vla-object (entlast)))))
    )
  
    (foreach item lst
      (if (= (vla-get-TagString item) "ИНФОРМАЦИЯ") (vla-put-TextString item info))
      (if (= (vla-get-TagString item) "ПРОИЗВОДИТЕЛЬ") (vla-put-TextString item manuf))
	  (if (= (vla-get-TagString item) "АРТИКУЛ") (vla-put-TextString item art))
	  (if (= (vla-get-TagString item) "НОМЕР") (vla-put-TextString item reference))
    )

); end_defun
