from django.db import models

class Breakpoint(models.Model):

    def __str__(self):
        return '{}:{:,}-{:,}'.format(self.chrom, self.start, self.end)

    sample =  models.ForeignKey(Sample, on_delete = models.PROTECT, null = True) 

    left_chrom = models.ForeignKey(Chromosome, on_delete = models.PROTECT, null = True, related_name = 'left_chrom') 
    left_coord = models.IntegerField()
    left_inverse = models.BooleanField(default = False)

    right_chrom = models.ForeignKey(Chromosome, on_delete = models.PROTECT, null = True, related_name = 'right_chrom') 
    right_coord = models.IntegerField()
    right_inverse = models.BooleanField(default = False)

    owner = models.ForeignKey(User, on_delete = models.PROTECT, null=True) 
    public = models.BooleanField(default = False)
    assembly = models.ForeignKey(Assembly, on_delete = models.PROTECT, related_name = 'breakpoints')
