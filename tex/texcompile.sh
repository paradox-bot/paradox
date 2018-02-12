cd tex
pdflatex out.tex
convert -background white -flatten -border 80 -density 500 -quality 100 out.pdf out.png

