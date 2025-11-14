(defun c:CreateREF (/ obj vla_obj V po bl_name osm)  
  (vl-load-com) ; загружаем функции расширения
    (setq obj (car (entsel "\nВыберите блок: ")))
    (if (not (= obj nil))
      (progn
        (setq vla_obj (vlax-ename->vla-object obj)) ; переводим в vla-object
        (setq lst (vlax-safearray->list
          (vlax-variant-value (vla-GetAttributes vla_obj)))
        )

        (foreach item lst
			(if (= (vla-get-TagString item) "ВН_ЖИЛА")  (setq wire (vla-get-TextString item)))
			(if (= (vla-get-TagString item) "ШКАФ")  (setq cabin (vla-get-TextString item)))
			(if (= (vla-get-TagString item) "КЛЕММНИК")  (setq clm (vla-get-TextString item)))
			(if (= (vla-get-TagString item) "УСТРОЙСТВО")  (setq clm (vla-get-TextString item)))
			(if (= (vla-get-TagString item) "КЛЕММА")  (setq clemma (vla-get-TextString item)))

	)
	(setq reference (strcat cabin ":" clm ":" clemma))
      );end progn
    ); end ifz

    (setq po (getpoint "\nУкажите базовую точку : "))        ; запрос координат базовой точки
    (command "_insert" "REF" po 1 1 0)  ; вставка блока
	
    (setq lst (vlax-safearray->list
        (vlax-variant-value (vla-GetAttributes (vlax-ename->vla-object (entlast)))))
    )
  
    (foreach item lst
      (if (= (vla-get-TagString item) "ID") (vla-put-TextString item reference))
    )

); end_defun
