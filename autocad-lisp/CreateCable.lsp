(defun c:CreateWire (/ obj vla_obj V po bl_name osm)  
  (vl-load-com) ; загружаем функции расширения
    (setq obj (car (entsel "\nВыберите блок: ")))
    (if (not (= obj nil))
      (progn
        (setq vla_obj (vlax-ename->vla-object obj)) ; переводим в vla-object
        (setq lst (vlax-safearray->list
          (vlax-variant-value (vla-GetAttributes vla_obj)))
        )

        (foreach item lst
			(if (= (vla-get-TagString item) "КАБЕЛЬ")  (setq cabel (vla-get-TextString item)))
			(if (= (vla-get-TagString item) "ЖИЛА")  (setq wire (vla-get-TextString item)))
			(if (= (vla-get-TagString item) "ШКАФ")  (setq cabin (vla-get-TextString item)))
			(if (= (vla-get-TagString item) "КЛЕММНИК")  (setq clm (vla-get-TextString item)))
			(if (= (vla-get-TagString item) "СЕЧЕНИЕ")  (setq section (vla-get-TextString item)))
			(if (= (vla-get-TagString item) "ТИП_КАБЕЛЯ")  (setq type_cabel (vla-get-TextString item)))
	  
	)
	(setq ending1 (strcat cabin ":" clm))
      );end progn
    ); end ifz

    (setq obj (car (entsel "\nВыберите блок: ")))
    (if (not (= obj nil))
      (progn
        (setq vla_obj (vlax-ename->vla-object obj)) ; переводим в vla-object
        (setq lst (vlax-safearray->list
          (vlax-variant-value (vla-GetAttributes vla_obj)))
        )

        (foreach item lst
	  (if (= (vla-get-TagString item) "ШКАФ")  (setq cabin (vla-get-TextString item)))
	  (if (= (vla-get-TagString item) "КЛЕММНИК")  (setq clm (vla-get-TextString item)))
	)
	(setq ending2 (strcat cabin ":" clm))
      );end progn
    ); end if

    (setq po (getpoint "\nУкажите базовую точку : "))        ; запрос координат базовой точки
    (command "_insert" "КАБЕЛЬ3" po 1 1 0)  ; вставка блока
	
    (setq lst (vlax-safearray->list
        (vlax-variant-value (vla-GetAttributes (vlax-ename->vla-object (entlast)))))
    )
  
    (foreach item lst
      (if (= (vla-get-TagString item) "НАПРАВЛЕНИЕ") (vla-put-TextString item cabel))
      ;;; (if (= (vla-get-TagString item) "ЖИЛА") (vla-put-TextString item wire))
      (if (= (vla-get-TagString item) "КЛЕММНИК1") (vla-put-TextString item ending1))
      (if (= (vla-get-TagString item) "КЛЕММНИК2") (vla-put-TextString item ending2))
      ;;; (if (= (vla-get-TagString item) "СЕЧЕНИЕ") (vla-put-TextString item section))
      ;;; (if (= (vla-get-TagString item) "ТИП_КАБЕЛЯ") (vla-put-TextString item type_cabel)) 
    )

); end_defun
