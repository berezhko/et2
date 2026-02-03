(defun c:save-blocks-geometry (/ block)
  (setq file_path (strcat (getvar "dwgprefix") (vl-filename-base (getvar "DWGNAME")) ".yaml"))
  (setq file_name (open-yaml-file file_path))
  (setq block (tblnext "BLOCK" t))   ; начать с первой записи
  (while block
    (save-block-geometry (cdr (assoc 2 block)) "DEFPOINTS" file_name)
    (setq block (tblnext "BLOCK"))   ; следующая запись
  )
  (close file_name)
)

(defun open-yaml-file (path)
  (if (findfile path)
    (vl-file-delete path)
  )
  (open path "w")
)

(defun save-block-geometry (blkname fine_layer file_name / blkdata ent)
  (if (setq blkdata (tblsearch "BLOCK" blkname))
    (yaml-block-description blkname blkdata fine_layer file_name)
  )
  (princ)
)

(defun yaml-block-description (blkname blkdata fine_layer file_name / ent)
  (setq ent (first-object blkdata))
  (output (strcat "- block_name: '" blkname "'") file_name)
  (output (strcat "  borders:") file_name)
  (output-elements "LINE" proc-line ent fine_layer file_name)
  (output (strcat "  contacts:") file_name)
  (output-elements "TEXT" proc-text ent fine_layer file_name)
)

(defun first-object (blkdata)
  (cdr (assoc -2 blkdata))
)

(defun output-elements (type-element process-element ent fine_layer file_name / entdata objtype layer)
  (while ent
    (setq entdata (entget ent)
          objtype (cdr (assoc 0 entdata))
          layer   (cdr (assoc 8 entdata)) ; имя слоя
    )
    ;; Обрабатываем ТОЛЬКО определенный слой и определенный тип элемена
    (if (and (= (strcase layer) (strcase fine_layer)) (= objtype type-element))
      (process-element entdata file_name)
    )
    (setq ent (entnext ent))
  )
)

(defun proc-text (entdata file_name / txtpt10 txtpt11 align-h align-v text-point)
  (setq txtpt10 (cdr (assoc 10 entdata))
        txtpt11 (cdr (assoc 11 entdata))
        align-h (cdr (assoc 72 entdata))
        align-v (cdr (assoc 73 entdata))
  )
  (if (or (/= align-h 0) (/= align-v 0))
    (setq text-point txtpt11)
    (setq text-point txtpt10)
  )
  (output 
    (strcat "    '" (cdr (assoc 1 entdata)) "': " (to-yaml text-point))
	file_name
  )
)

(defun proc-line (entdata file_name / point1 point2)
  (setq point1 (cdr (assoc 10 entdata))
        point2 (cdr (assoc 11 entdata))
  )
  (output
    (strcat "    - [" (to-yaml point1) ", " (to-yaml point2) "]")
	 file_name
  )
)

(defun to-yaml (pt)
  (strcat "[" (rtos (car pt) 2 2) ", " (rtos (cadr pt) 2 2) "]")
)

(defun output (str file_name)
  (write-line str file_name)
)