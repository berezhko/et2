for nb in ВнешниеСоединения.ipynb ДиаметрыПроходок.ipynb ЗагрузкаУстройств.ipynb Шкафы.ipynb ЭКРА.ipynb ФайлыБлокиAutocad.ipynb
do
  jupyter nbconvert --to script $nb
  black `basename $nb .ipynb`.py
done
