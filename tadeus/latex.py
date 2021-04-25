    

   

            


"""
        for gene_name, gene in results:

            phenotypes = gene['phenotypes']

            if not phenotypes:
                continue

            f_out.write('\\begin{center}\n')
            f_out.write('\t\\begin{longtable}{ | p{3cm} |  p{10cm} |}\n')

            f_out.write('\t\t\\hline\n')
            f_out.write('\\multicolumn{2}{ |c| }{' + gene_name + '} \\\\\n')

            f_out.write('\t\t\\hline\n')
            f_out.write('\t\t Name  & Definition and comments \\\\\n')
            f_out.write('\t\t\\hline\n')


            for phenotype in phenotypes:



                f_out.write(phenotype.name)
                f_out.write(' \href{' + phenotype.url + '}{' + phenotype.pheno_id +'}')
                f_out.write(' & ')

                info = []

                if phenotype.definition:
                    definition = 'Definition: ' + phenotype.definition.replace('%', '\%')
                    info.append(definition)
                if phenotype.comment:
                    comment = 'Comment: ' + phenotype.comment.replace('%', '\%')
                    info.append(comment)

                if phenotype.pheno_id in ('HP:0000006', 'HP:0000007'):
                    info = []

                if len(info) > 0:
                    f_out.write(info[0])

                f_out.write('\\\\\n')

                if len(info) == 2:
                    f_out.write(' & ')
                    f_out.write(info[1])                                         
                    f_out.write('\\\\\n')     

                f_out.write('\t\t\\hline\n')               
        
            f_out.write("\\end{longtable} \\end{center}")
"""